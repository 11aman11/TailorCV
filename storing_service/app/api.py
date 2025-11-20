from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.service import store_cv, get_cv_by_id

router = APIRouter()

class StoreCVRequest(BaseModel):
    structured_json: dict
    cv_text: str

class StoreCVResponse(BaseModel):
    cv_id: str
    status: str
    message: str

@router.post("/internal/store_cv", response_model=StoreCVResponse)
async def store_cv_endpoint(request: StoreCVRequest):
    """
    Store structured CV in MongoDB with deduplication
    
    Args:
        structured_json: Output from GeminiService (metadata + structured_sections)
        cv_text: Original raw CV text
        
    Returns:
        cv_id (SHA256 hash) and status
    """
    try:
        result = store_cv(request.structured_json, request.cv_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store CV: {str(e)}")

@router.get("/internal/get_cv/{cv_id}")
async def get_cv_endpoint(cv_id: str):
    """
    Retrieve CV by cv_id
    
    Args:
        cv_id: SHA256 hash of CV text
        
    Returns:
        Complete CV document
    """
    try:
        cv = get_cv_by_id(cv_id)
        return cv
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve CV: {str(e)}")

