import hashlib
from datetime import datetime
from app.db_mongo import find_cv_by_id, insert_cv_document, find_all_cvs

def store_cv(structured_json: dict, cv_text: str) -> dict:
    """
    Store CV in MongoDB with hash-based deduplication
    
    Args:
        structured_json: Structured CV data from GeminiService
            Contains: metadata and structured_sections
        cv_text: Original raw CV text (for hash calculation)
        
    Returns:
        Dictionary with cv_id and status
    """
    # Calculate SHA256 hash of raw text
    cv_id = hashlib.sha256(cv_text.encode('utf-8')).hexdigest()
    
    # Check for duplicates
    existing = find_cv_by_id(cv_id)
    if existing:
        return {
            "cv_id": cv_id,
            "status": "already_exists",
            "message": "CV with this content already exists"
        }
    
    # Create document
    document = {
        "cv_id": cv_id,
        "cv_text": cv_text,
        "metadata": structured_json.get("metadata", {}),
        "structured_sections": structured_json.get("structured_sections", {}),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert into MongoDB
    insert_cv_document(document)
    
    return {
        "cv_id": cv_id,
        "status": "stored",
        "message": "CV stored successfully"
    }

def get_cv_by_id(cv_id: str) -> dict:
    """Retrieve CV by cv_id"""
    cv = find_cv_by_id(cv_id)
    if not cv:
        raise ValueError(f"CV with id {cv_id} not found")
    return cv

def get_all_cvs() -> list:
    """
    Get all CVs for dropdown selection
    
    Returns:
        List of CVs with cv_id, filename, created_at
    """
    cvs = find_all_cvs()
    
    # Format for frontend
    formatted_cvs = []
    for cv in cvs:
        formatted_cvs.append({
            "cv_id": cv.get("cv_id"),
            "filename": cv.get("metadata", {}).get("filename", "Unknown"),
            "created_at": cv.get("created_at").isoformat() if cv.get("created_at") else None
        })
    
    return formatted_cvs

