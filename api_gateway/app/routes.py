from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import io

# Import HTTP clients
from app.clients import gemini_client, storing_client

# Try to import PyPDF2 for PDF extraction
try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

router = APIRouter()

# ==========================================
# Request/Response Models
# ==========================================

class UploadCVRequest(BaseModel):
    cv_text: str

class KeywordsRequest(BaseModel):
    cv_id: str
    job_description: str

class ScoreRequest(BaseModel):
    cv_id: str
    job_description: str

# ==========================================
# Public Endpoints
# ==========================================

@router.get("/my_cvs")
async def get_my_cvs():
    """
    Get all CVs for dropdown selection
    
    Returns:
        List of CVs with cv_id, filename, created_at
    """
    try:
        cvs = storing_client.get_all_cvs()
        return {
            "success": True,
            "cvs": cvs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch CVs: {str(e)}")

@router.post("/upload_cv_text")
async def upload_cv_text(request: UploadCVRequest):
    """
    Upload CV as text
    
    Flow:
    1. Structure CV with GeminiService
    2. Store CV in StoringService
    3. Return cv_id
    """
    try:
        # Structure CV
        structured = gemini_client.structure_cv(request.cv_text)
        
        # Store CV
        stored = storing_client.store_cv(structured, request.cv_text)
        
        return {
            "success": True,
            "message": "CV uploaded successfully!",
            "cv_id": stored["cv_id"],
            "status": stored["status"],
            "filename": structured["metadata"].get("filename", "Unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload CV: {str(e)}")

@router.post("/upload_cv_pdf")
async def upload_cv_pdf(file: UploadFile = File(...)):
    """
    Upload CV as PDF file
    
    Flow:
    1. Extract text from PDF
    2. Structure CV with GeminiService
    3. Store CV in StoringService
    4. Return cv_id
    """
    if not PDF_SUPPORT:
        raise HTTPException(status_code=500, detail="PDF support not available. Install PyPDF2.")
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Extract text from PDF
        pdf = PdfReader(io.BytesIO(pdf_bytes))
        cv_text = ""
        for page in pdf.pages:
            cv_text += page.extract_text() + "\n"
        
        if not cv_text.strip():
            raise ValueError("Could not extract text from PDF. The file might be scanned or empty.")
        
        # Structure CV
        structured = gemini_client.structure_cv(cv_text)
        
        # Override filename with uploaded file name
        structured["metadata"]["filename"] = file.filename
        
        # Store CV
        stored = storing_client.store_cv(structured, cv_text)
        
        return {
            "success": True,
            "message": "CV uploaded successfully!",
            "cv_id": stored["cv_id"],
            "status": stored["status"],
            "filename": file.filename
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@router.post("/keywords")
async def get_keywords(request: KeywordsRequest):
    """
    Get missing keywords
    
    Flow:
    1. Call GeminiService /internal/missing_keywords
    2. Return result
    """
    try:
        result = gemini_client.get_missing_keywords(request.cv_id, request.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze keywords: {str(e)}")

@router.post("/score")
async def get_score(request: ScoreRequest):
    """
    Get CV score
    
    Flow:
    1. Call GeminiService /internal/score
    2. Return result
    """
    try:
        result = gemini_client.get_score(request.cv_id, request.job_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate score: {str(e)}")
