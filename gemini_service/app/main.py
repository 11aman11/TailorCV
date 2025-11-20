from fastapi import FastAPI
from app.api import router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="GeminiService",
    description="LLM operations for CV analysis and structuring",
    version="1.0.0"
)

app.include_router(router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "GeminiService",
        "version": "1.0.0"
    }

