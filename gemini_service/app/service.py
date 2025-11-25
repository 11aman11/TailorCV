from datetime import datetime
from app.llm_client import call_gemini_to_structure_cv, call_gemini_for_missing_keywords, call_gemini_for_score
from app.storing_client import get_cv

def structure_cv(cv_text: str) -> dict:
    """
    Structure a CV using Gemini AI
    
    Args:
        cv_text: Raw CV text string
        
    Returns:
        Dictionary with metadata and structured_sections
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text cannot be empty")
    
    # Generate metadata
    metadata = generate_metadata(cv_text)
    
    # Extract structured sections using Gemini
    structured_sections = call_gemini_to_structure_cv(cv_text)
    
    return {
        "metadata": metadata,
        "structured_sections": structured_sections
    }

def generate_metadata(cv_text: str) -> dict:
    """Generate metadata about the CV"""
    section_keywords = [
        'education', 'experience', 'skills', 'projects',
        'certifications', 'awards', 'leadership', 'summary'
    ]
    sections_detected = sum(
        1 for keyword in section_keywords
        if keyword.lower() in cv_text.lower()
    )
    
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "character_count": len(cv_text),
        "word_count": len(cv_text.split()),
        "sections_detected": sections_detected,
        "parser_version": "1.0.0",
        "extraction_method": "gemini-2.5-flash"
    }

def find_missing_keywords(cv_id: str, job_description: str) -> dict:
    """
    Find missing keywords by comparing CV with job description
    
    Args:
        cv_id: CV identifier (SHA256 hash)
        job_description: Job description text
        
    Returns:
        Dictionary with cv_id, filename, keywords_you_have, and keywords_missing
        
    Raises:
        ValueError: If job description is empty or CV not found
    """
    # Validate job description
    if not job_description or not job_description.strip():
        raise ValueError("Please provide a job description")
    
    # Fetch CV from StoringService
    try:
        cv_data = get_cv(cv_id)
    except Exception as e:
        if "CV not found" in str(e):
            raise ValueError("CV not found")
        raise Exception(f"Failed to fetch CV: {str(e)}")
    
    # Extract structured sections
    structured_sections = cv_data.get("structured_sections", {})
    
    # Get filename from metadata (if available)
    metadata = cv_data.get("metadata", {})
    filename = metadata.get("filename", "Unknown")
    
    # Call Gemini to analyze keywords
    keyword_analysis = call_gemini_for_missing_keywords(structured_sections, job_description)
    
    # Return result with metadata
    return {
        "cv_id": cv_id,
        "filename": filename,
        "keywords_you_have": keyword_analysis["keywords_you_have"],
        "keywords_missing": keyword_analysis["keywords_missing"]
    }

def calculate_score(cv_id: str, job_description: str) -> dict:
    """
    Calculate CV score by comparing with job description
    
    Args:
        cv_id: CV identifier (SHA256 hash)
        job_description: Job description text
        
    Returns:
        Dictionary with cv_id, filename, overall_score, category_scores, strengths, gaps, recommendations
        
    Raises:
        ValueError: If job description is empty or CV not found
    """
    # Validate job description
    if not job_description or not job_description.strip():
        raise ValueError("Please provide a job description")
    
    # Fetch CV from StoringService
    try:
        cv_data = get_cv(cv_id)
    except Exception as e:
        if "CV not found" in str(e):
            raise ValueError("CV not found")
        raise Exception(f"Failed to fetch CV: {str(e)}")
    
    # Extract structured sections
    structured_sections = cv_data.get("structured_sections", {})
    
    # Get filename from metadata (if available)
    metadata = cv_data.get("metadata", {})
    filename = metadata.get("filename", "Unknown")
    
    # Call Gemini to score CV
    score_result = call_gemini_for_score(structured_sections, job_description)
    
    # Return result with metadata
    return {
        "cv_id": cv_id,
        "filename": filename,
        "overall_score": score_result["overall_score"],
        "max_score": score_result["max_score"],
        "rating": score_result["rating"],
        "category_scores": score_result["category_scores"],
        "strengths": score_result["strengths"],
        "gaps": score_result["gaps"],
        "recommendations": score_result["recommendations"]
    }

