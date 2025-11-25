import os
import requests
from dotenv import load_dotenv

load_dotenv()

STORING_SERVICE_URL = os.getenv("STORING_SERVICE_URL", "http://localhost:8001")

def process_cv_for_embedding(cv_id: str):
    """
    Process CV for embedding (called by RabbitMQ consumer)
    
    Flow:
    1. Fetch CV from StoringService
    2. Extract structured_sections
    3. Chunk sections (TODO: implement chunking)
    4. Embed chunks (TODO: implement embedding)
    5. Upload to Pinecone (TODO: implement Pinecone upload)
    
    Args:
        cv_id: CV identifier
    """
    print(f"Processing CV for embedding: {cv_id}")
    
    try:
        # Fetch CV from StoringService
        response = requests.get(
            f"{STORING_SERVICE_URL}/internal/get_cv/{cv_id}",
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch CV: {response.status_code}")
        
        cv_data = response.json()
        structured_sections = cv_data.get("structured_sections", {})
        
        print(f"Fetched CV: {cv_id}")
        print(f"Sections found: {list(structured_sections.keys())}")
        
        # TODO: Implement chunking logic
        # chunks = chunk_structured_sections(structured_sections, cv_id)
        
        # TODO: Implement embedding
        # embedded_chunks = embed_chunks(chunks)
        
        # TODO: Upload to Pinecone
        # upsert_to_pinecone(embedded_chunks)
        
        print(f"CV processing complete: {cv_id}")
        
    except Exception as e:
        print(f"Error processing CV {cv_id}: {e}")
        raise
