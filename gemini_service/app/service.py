from datetime import datetime
from app.llm_client import call_gemini_to_structure_cv

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

