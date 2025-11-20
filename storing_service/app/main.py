from fastapi import FastAPI
from app.api import router
from app.db_mongo import create_indexes
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="StoringService",
    description="CV storage and retrieval with MongoDB",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    """Initialize database indexes on startup"""
    create_indexes()

app.include_router(router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "StoringService",
        "version": "1.0.0"
    }

