from pinecone import Pinecone
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / "infra" / ".env"
load_dotenv(ENV_PATH)

api_key = os.environ["PINECONE_API_KEY"]
index_name = os.environ["PINECONE_INDEX_NAME"]

pc = Pinecone(api_key=api_key)
index = pc.Index(index_name)

print("Deleting all vectors...")
index.delete(deleteAll=True)
print("Done.")