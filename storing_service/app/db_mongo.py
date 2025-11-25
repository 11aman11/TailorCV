import os
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI not found in environment variables")

client = MongoClient(MONGODB_URI)
db = client["tailorcv_db"]
collection = db["cvs"]

def create_indexes():
    """Create indexes on cv_id and created_at"""
    try:
        collection.create_index("cv_id", unique=True)
        collection.create_index([("created_at", DESCENDING)])
        print("Database indexes created successfully")
    except Exception as e:
        print(f"Index creation (likely already exist): {str(e)}")

def find_cv_by_id(cv_id: str) -> dict:
    """Find CV by cv_id hash"""
    return collection.find_one({"cv_id": cv_id}, {"_id": 0})

def insert_cv_document(document: dict) -> str:
    """
    Insert CV document into MongoDB
    
    Args:
        document: Complete CV document with all fields
        
    Returns:
        cv_id of inserted document
        
    Raises:
        DuplicateKeyError if cv_id already exists
    """
    collection.insert_one(document)
    return document["cv_id"]

def find_latest_cv() -> dict:
    """Find most recently created CV"""
    return collection.find_one(
        sort=[("created_at", DESCENDING)],
        projection={"_id": 0}
    )

def find_all_cvs() -> list:
    """
    Find top 10 most recently uploaded CVs (for dropdown selection)
    
    Returns:
        List of up to 10 CVs with limited fields (cv_id, filename, created_at)
        Sorted by most recent first
    """
    cvs = collection.find(
        {},
        {"_id": 0, "cv_id": 1, "metadata.filename": 1, "created_at": 1}
    ).sort("created_at", DESCENDING).limit(10)
    
    return list(cvs)

