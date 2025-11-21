# API Gateway - Public Endpoints
# Defines all 7 public endpoints exposed to clients
# 
# Endpoints:
# 1. POST /attach_cv - Upload and structure a CV
# 2. POST /keywords - Get missing keywords for a CV against a job description
# 3. POST /score - Score a CV against a job description
# 4. POST /similar_cvs - Find top-k similar CVs to a job description
# 5. POST /tailored_points - Generate tailored bullet points
# 6. GET /my_cv - Get the latest uploaded CV
# 7. POST /upload_cvs (optional, later) - Batch upload multiple CVs
#
# Responsibilities:
# - Route orchestration ONLY (no business logic)
# - Call appropriate services via HTTP clients
# - Combine responses from multiple services when needed
# - Return formatted responses to client

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from .clients import gemini_client, storing_client, vector_client

router = APIRouter(tags=["public"])

# --------- Pydantic models (public API contracts) ---------


class AttachCvResponse(BaseModel):
    status: str = "success"
    cv_id: str = Field(..., description="Identifier of stored CV")
    message: str = "CV uploaded"


class KeywordsRequest(BaseModel):
    jd_text: str
    cv_id: str


class KeywordsResponse(BaseModel):
    missing_keywords: List[str]
    explanation: Optional[str] = None


class ScoreRequest(BaseModel):
    jd_text: str
    cv_id: str


class ScoreResponse(BaseModel):
    score: float
    explanation: str


class SimilarCvsRequest(BaseModel):
    jd_text: str
    top_k: int = 3


class SimilarCvItem(BaseModel):
    cv_id: str
    score: float


class SimilarCvsResponse(BaseModel):
    results: List[SimilarCvItem]


class TailoredPointsRequest(BaseModel):
    jd_text: str
    # optional: directly pass chunks (if you already have them)
    chunks: Optional[List[Dict[str, Any]]] = None


class TailoredPointsResponse(BaseModel):
    bullet_points: List[str]


class MyCvResponse(BaseModel):
    cv_id: str
    structured_cv: Dict[str, Any]
    created_at: Optional[str] = None


# --------- Routes ---------


@router.post("/attach_cv", response_model=AttachCvResponse)
async def attach_cv(
    cv_file: Optional[UploadFile] = File(default=None),
    cv_text: Optional[str] = Form(default=None),
):
    """
    1. Take either cv_file or cv_text.
    2. Call GeminiService to structure the CV.
    3. Call StoringService to save it.
    4. Return cv_id to client.
    """
    if cv_file is None and (cv_text is None or cv_text.strip() == ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'cv_file' or 'cv_text' must be provided.",
        )

    # Resolve CV text
    if cv_file is not None:
        raw_bytes = await cv_file.read()
        resolved_text = raw_bytes.decode("utf-8", errors="ignore")
    else:
        resolved_text = (cv_text or "").strip()

    if not resolved_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolved CV text is empty.",
        )

    # Structure CV
    try:
        gemini_result = await gemini_client.structure_cv(resolved_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GeminiService error: {e}",
        )

    structured_cv = gemini_result.get("structured_cv", gemini_result)

    # Store CV
    try:
        store_result = await storing_client.store_cv(
            structured_cv=structured_cv,
            cv_text=resolved_text,
            user_id="demo-user-1",  # TODO: real user id when auth is added
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"StoringService error: {e}",
        )

    cv_id = store_result.get("cv_id")
    if not cv_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="StoringService response missing 'cv_id'.",
        )

    return AttachCvResponse(
        cv_id=cv_id,
        message="CV uploaded and stored successfully.",
    )


@router.post("/keywords", response_model=KeywordsResponse)
async def get_missing_keywords(body: KeywordsRequest):
    """
    Get missing keywords for a CV vs job description.
    """
    try:
        result = await gemini_client.missing_keywords(
            jd_text=body.jd_text, cv_id=body.cv_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GeminiService error: {e}",
        )

    return KeywordsResponse(
        missing_keywords=result.get("missing_keywords", []),
        explanation=result.get("explanation"),
    )


@router.post("/score", response_model=ScoreResponse)
async def score_cv(body: ScoreRequest):
    """
    Score a CV vs job description.
    """
    try:
        result = await gemini_client.score(jd_text=body.jd_text, cv_id=body.cv_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GeminiService error: {e}",
        )

    return ScoreResponse(
        score=result.get("score", 0.0),
        explanation=result.get("explanation", ""),
    )


@router.post("/similar_cvs", response_model=SimilarCvsResponse)
async def similar_cvs(body: SimilarCvsRequest):
    """
    Retrieve top-k similar CVs using the VectorService.
    """
    try:
        result = await vector_client.search_top_k_cvs(
            jd_text=body.jd_text, top_k=body.top_k
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"VectorService error: {e}",
        )

    items = [
        SimilarCvItem(cv_id=item["cv_id"], score=item["score"])
        for item in result.get("results", [])
    ]
    return SimilarCvsResponse(results=items)


@router.post("/tailored_points", response_model=TailoredPointsResponse)
async def tailored_points(body: TailoredPointsRequest):
    """
    Generate tailored bullet points.
    If chunks are not provided, fetch similar chunks from VectorService first.
    """
    chunks = body.chunks
    if chunks is None:
        try:
            vec_result = await vector_client.similar_chunks(jd_text=body.jd_text)
            chunks = vec_result.get("chunks", [])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"VectorService error: {e}",
            )

    try:
        result = await gemini_client.tailored_bullets(
            jd_text=body.jd_text, chunks=chunks
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GeminiService error: {e}",
        )

    return TailoredPointsResponse(
        bullet_points=result.get("bullet_points", []),
    )


@router.get("/my_cv", response_model=MyCvResponse)
async def my_cv():
    """
    Get the latest uploaded CV for the current user.
    Currently uses a hard-coded user id.
    """
    try:
        latest = await storing_client.get_latest_cv(user_id="demo-user-1")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"StoringService error: {e}",
        )

    cv_id = latest.get("cv_id")
    structured_cv = latest.get("structured_cv")
    if not cv_id or structured_cv is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid latest CV data from StoringService.",
        )

    return MyCvResponse(
        cv_id=cv_id,
        structured_cv=structured_cv,
        created_at=latest.get("created_at"),
    )


@router.post("/upload_cvs")
async def upload_cvs_not_implemented():
    """
    Optional: batch upload multiple CVs.
    For now, explicitly mark as not implemented so clients know it's a stub.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Batch upload is not implemented yet.",
    )