from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.service import structure_cv

router = APIRouter()

class StructureCVRequest(BaseModel):
    cv_text: str

class StructureCVResponse(BaseModel):
    metadata: dict
    structured_sections: dict

@router.post("/internal/structure_cv", response_model=StructureCVResponse)
async def structure_cv_endpoint(request: StructureCVRequest):
    """
    Structure raw CV text into JSON format
    
    Args:
        cv_text: Raw CV text string
        
    Returns:
        metadata and structured_sections
    """
    try:
        result = structure_cv(request.cv_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to structure CV: {str(e)}")

