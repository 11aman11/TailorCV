import json
import hashlib
import os
import sys
from pathlib import Path
from typing import Iterator, Dict, Any, List

from dotenv import load_dotenv
from pymongo import MongoClient
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import torch

# -----------------------------
# Config
# -----------------------------
DATASET_PATH = Path("Dataset/master_resumes.jsonl")  # adjust if needed
MONGO_COLLECTION_NAME = "dataset_cvs"               # new collection
MODEL_NAME = "BAAI/bge-base-en-v1.5"
EMBED_DIM = 768

# -----------------------------
# Import vector_service embedder
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from vector_service.app import embedder as vs_embedder

# -----------------------------
# Embedding model state (global)
# -----------------------------
_device = "cuda" if torch.cuda.is_available() else "cpu"
_model: SentenceTransformer | None = None

# -----------------------------
# Helpers
# -----------------------------
def build_structured_sections_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform dataset record into something similar to Gemini's structured_sections
    so we can reuse vector_service/app/embedder.py chunking logic.
    """
    structured: Dict[str, Any] = {}

    # ----- summary / contact -----
    pi = record.get("personal_info", {}) or {}
    summary = pi.get("summary")
    if summary:
        structured["summary"] = {"text": summary}

    contact = {}
    name = pi.get("name")
    email = pi.get("email")
    phone = pi.get("phone")
    linkedin = pi.get("linkedin")
    github = pi.get("github")

    if name:
        contact["name"] = name
    if email:
        contact["email"] = email
    if phone:
        contact["phone"] = phone
    if linkedin:
        contact["linkedin"] = linkedin
    if github:
        contact["github"] = github

    if contact:
        structured["contact"] = contact

    # ----- education -----
    edu_list = []
    for edu in record.get("education", []) or []:
        inst = edu.get("institution", {}) or {}
        degree = edu.get("degree", {}) or {}

        edu_obj = {
            "institution": inst.get("name"),
            "degree": degree.get("level") or degree.get("name") or degree.get("title"),
            "field": degree.get("field"),
            "gpa": edu.get("gpa"),
            "location": inst.get("location"),
            "start_date": edu.get("start_date"),
            "end_date": edu.get("end_date"),
        }

        # keep only if there is *something* non-empty
        if any(v for v in edu_obj.values()):
            edu_list.append(edu_obj)

    if edu_list:
        structured["education"] = edu_list

    # ----- experience -----
    exp_list = []
    for job in record.get("experience", []) or []:
        bullets = job.get("responsibilities") or []
        if isinstance(bullets, str):
            bullets = [bullets]

        exp_obj = {
            "company": job.get("company"),
            "title": job.get("title"),
            "location": job.get("location"),
            "bullets": bullets,
            "start_date": job.get("start_date"),
            "end_date": job.get("end_date"),
        }

        if any([exp_obj["company"], exp_obj["title"], bullets]):
            exp_list.append(exp_obj)

    if exp_list:
        structured["experience"] = exp_list

    # ----- projects -----
    proj_list = []
    for proj in record.get("projects", []) or []:
        bullets = proj.get("responsibilities") or proj.get("bullets") or []
        if isinstance(bullets, str):
            bullets = [bullets]

        proj_obj = {
            "name": proj.get("name"),
            "description": proj.get("description"),
            "impact": proj.get("impact"),
            "technologies": proj.get("technologies", []),
            "link": proj.get("link"),
            "bullets": bullets,
        }

        if any([proj_obj["name"], proj_obj["description"], proj_obj["impact"], bullets]):
            proj_list.append(proj_obj)

    if proj_list:
        structured["projects"] = proj_list

    # ----- skills -----
    skills_dict: Dict[str, List[str]] = {}
    skills = record.get("skills", {}) or {}
    tech = skills.get("technical", {}) if isinstance(skills, dict) else {}

    if isinstance(tech, dict):
        for cat_name, cat_list in tech.items():
            if not isinstance(cat_list, list):
                continue
            names: List[str] = []
            for s in cat_list:
                if isinstance(s, dict) and s.get("name"):
                    names.append(s["name"])
                elif isinstance(s, str):
                    names.append(s)
            if names:
                skills_dict[cat_name] = names

    if skills_dict:
        structured["skills"] = skills_dict

    # you can extend this with leadership/certifications if present in dataset

    return structured


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def compute_cv_id(cv_text: str) -> str:
    return hashlib.sha256(cv_text.encode("utf-8")).hexdigest()


def record_to_cv_text(record: Dict[str, Any]) -> str:
    """
    Build a human-readable CV text from the structured JSON.
    This is what we store as cv_text in Mongo.
    """
    parts: List[str] = []

    # Personal info
    pi = record.get("personal_info", {}) or {}
    name = pi.get("name")
    if name:
        parts.append(name)

    summary = pi.get("summary")
    if summary:
        parts.append(summary)

    # Education
    for edu in record.get("education", []) or []:
        inst = edu.get("institution", {}) or {}
        degree = edu.get("degree", {}) or {}
        line = " ".join(
            x
            for x in [
                degree.get("level"),
                degree.get("field"),
                inst.get("name"),
                inst.get("location"),
            ]
            if x
        )
        if line:
            parts.append(line)

    # Experience
    for job in record.get("experience", []) or []:
        title = job.get("title")
        company = job.get("company")
        line = " - ".join(x for x in [title, company] if x)
        if line:
            parts.append(line)

        resp = job.get("responsibilities") or []
        if isinstance(resp, list):
            parts.extend(resp)
        elif isinstance(resp, str):
            parts.append(resp)

    # Skills (technical programming languages etc.)
    skills = record.get("skills", {}) or {}
    tech = skills.get("technical", {}) if isinstance(skills, dict) else {}
    if isinstance(tech, dict):
        prog = tech.get("programming_languages", []) or []
        skill_names = [
            s.get("name")
            for s in prog
            if isinstance(s, dict) and s.get("name")
        ]
        if skill_names:
            parts.append("Programming languages: " + ", ".join(skill_names))

    # Projects
    for proj in record.get("projects", []) or []:
        name = proj.get("name")
        desc = proj.get("description")
        impact = proj.get("impact")
        line = " - ".join(x for x in [name, desc, impact] if x)
        if line:
            parts.append(line)

    return "\n".join(p for p in parts if p)


def main():
    # -----------------------------
    # Load env from infra/.env
    # -----------------------------
    ROOT_DIR = Path(__file__).resolve().parents[1]  # TailorCV/
    ENV_PATH = ROOT_DIR / "infra" / ".env"
    load_dotenv(ENV_PATH)

    mongo_uri = os.environ["MONGODB_URI"]
    db_name = os.environ.get("MONGODB_DB_NAME", "tailorcv_db")
    pinecone_api_key = os.environ["PINECONE_API_KEY"]
    pinecone_index_name = os.environ["PINECONE_INDEX_NAME"]

    # -----------------------------
    # MongoDB
    # -----------------------------
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[db_name]
    collection = db[MONGO_COLLECTION_NAME]

    # -----------------------------
    # Pinecone
    # -----------------------------
    pc = Pinecone(api_key=pinecone_api_key)

    # Ensure index exists; if you already created tailorcv-cv-chunks,
    # this "create_index" block will simply be skipped.
    existing = [idx["name"] for idx in pc.list_indexes()]
    if pinecone_index_name not in existing:
        pc.create_index(
            name=pinecone_index_name,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    index = pc.Index(pinecone_index_name)

    # -----------------------------
    # Iterate JSONL
    # -----------------------------
    print(f"Reading resumes from {DATASET_PATH} ...")

    for i, record in enumerate(iter_jsonl(DATASET_PATH), start=1):
        # Build cv_text from structured fields (for Mongo + cv_id)
        cv_text = record_to_cv_text(record)
        if not cv_text:
            print(f"[WARN] Line {i}: could not build cv_text, skipping")
            continue

        provided_id = record.get("id")
        cv_id = provided_id or compute_cv_id(cv_text)

        print(f"[{i}] Processing cv_id={cv_id[:8]}...")

        # 1) Insert into Mongo (if not exists)
        existing_doc = collection.find_one({"cv_id": cv_id})
        if existing_doc:
            print("  - already in Mongo")
        else:
            doc = {
                "cv_id": cv_id,
                "cv_text": cv_text,
                # keep original dataset record or structured_sections if you prefer
                "structured_sections": record,
                "metadata": {
                    "source": "dataset",
                    "dataset_id": provided_id,
                },
                "created_at": None,
                "updated_at": None,
            }
            collection.insert_one(doc)
            print(
                f"  - inserted into Mongo collection '{MONGO_COLLECTION_NAME}'"
            )

        # -----------------------------
        # 2) Build Gemini-style structured_sections
        #     and run through the SAME chunk pipeline
        #     as vector_service/embedder.py
        # -----------------------------
        structured_sections = build_structured_sections_from_record(record)

        if not structured_sections:
            print("  - no structured sections built, skipping Pinecone")
            continue

        # 2a) base chunks (summary, skills, education, etc.)
        base_chunks = vs_embedder.chunk_structured_sections(
            structured_sections, cv_id
        )

        # 2b) experience bullets
        exp_list = structured_sections.get("experience", []) or []
        exp_chunks = vs_embedder.chunk_experience_bullets(exp_list, cv_id)

        # 2c) projects bullets
        proj_list = structured_sections.get("projects", []) or []
        proj_chunks = vs_embedder.chunk_projects_bullets(proj_list, cv_id)

        all_chunks: List[Dict[str, Any]] = base_chunks + exp_chunks + proj_chunks

        if not all_chunks:
            print("  - no chunks produced, skipping Pinecone")
            continue

        # -----------------------------
        # 3) Embed using EXACT same pipeline as vector_service
        # -----------------------------
        all_chunks = vs_embedder.embed_chunks(all_chunks)

        # -----------------------------
        # 4) Upsert to Pinecone
        # -----------------------------
        vectors = []
        for idx, chunk in enumerate(all_chunks):
            vector_id = f"{cv_id}_{chunk['section']}_{idx}"

            text = chunk.get("text", "")
            raw_metadata = (chunk.get("metadata") or {}).copy()

            # Tag as dataset if not already
            if "source" not in raw_metadata:
                raw_metadata["source"] = "dataset"

            # --- sanitize metadata for Pinecone ---
            clean_metadata: Dict[str, Any] = {}
            for k, v in raw_metadata.items():
                if v is None:
                    # drop nulls – Pinecone doesn't allow them
                    continue
                if isinstance(v, (str, int, float, bool)):
                    clean_metadata[k] = v
                elif isinstance(v, list):
                    # Pinecone only allows list of strings, so coerce
                    clean_metadata[k] = [str(x) for x in v if x is not None]
                else:
                    # Fallback: stringify anything weird (dicts, objects, etc.)
                    clean_metadata[k] = str(v)

            # Final metadata we send to Pinecone
            final_metadata = {
                "cv_id": cv_id,
                "section": chunk["section"],
                "raw_text": text,
                **clean_metadata,
            }

            vectors.append(
                {
                    "id": vector_id,
                    "values": chunk["embedding"],
                    "metadata": final_metadata,
                }
            )

        index.upsert(vectors=vectors)
        print(
            f"  - upserted {len(vectors)} vectors into "
            f"'{pinecone_index_name}'"
        )

    print("Done ingesting dataset.")


if __name__ == "__main__":
    main()