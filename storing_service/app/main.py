from fastapi import FastAPI
from app.api import router
from app.db_mongo import create_indexes
from app.events import close_rabbitmq_connection
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

@app.on_event("shutdown")
def shutdown_event():
    """Clean up connections on shutdown"""
    close_rabbitmq_connection()

app.include_router(router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "StoringService",
        "version": "1.0.0"
    }

