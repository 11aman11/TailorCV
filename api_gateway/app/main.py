# API Gateway - FastAPI Application Entry Point
# This is the main entry point for the API Gateway service
# Responsibilities:
# - Initialize FastAPI application
# - Register routes from routes.py
# - Configure CORS, middleware
# - Health check endpoint

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router as api_router

app = FastAPI(
    title="TailorCV API Gateway",
    version="0.1.0",
    description="Public API Gateway for TailorCV",
)

# CORS – adjust origins later if you have a real frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}