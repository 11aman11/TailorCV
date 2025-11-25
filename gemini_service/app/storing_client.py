import os
import requests
from dotenv import load_dotenv

load_dotenv()

STORING_SERVICE_URL = os.getenv("STORING_SERVICE_URL", "http://localhost:8001")

def get_cv(cv_id: str) -> dict:
    """
    Fetch CV from StoringService by cv_id
    
    Args:
        cv_id: The CV identifier (SHA256 hash)
        
    Returns:
        Dictionary with cv_id, cv_text, metadata, and structured_sections
        
    Raises:
        Exception: If CV not found or StoringService is unreachable
    """
    url = f"{STORING_SERVICE_URL}/internal/get_cv/{cv_id}"
    
    response = requests.get(url, timeout=10)
    
    if response.status_code == 404:
        raise Exception("CV not found")
    elif response.status_code != 200:
        raise Exception(f"StoringService error: {response.status_code}")
    
    return response.json()

