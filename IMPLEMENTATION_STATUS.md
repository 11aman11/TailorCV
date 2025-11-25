# TailorCV - Implementation Status

**Date:** November 19, 2025  
**Phase:** Internal Services Implementation (Phase 1) 

---

## What I Implemented so far
Check diagram, for now only Service 1 - Storing Service (this): 
only 1.1 (StoreCv) and 1.2 (getCV) are done. 
from Service 2 - Gemini Service:
2.1 (StructureCV) is done
2.2 (Missing Keywords) is done
2.3 (Score) - Not yet implemented

We still have to implement full flow of exposed APIs (client) and all the interal APIs and system flow for those exposed APIs to travel within those services by their own APIs. (For more info reach out to me - Aman before you start from somehwhere to make things clear)

### Services Completed
- **GeminiService** - CV structuring using Gemini AI
- **StoringService** - CV storage with MongoDB and hash-based deduplication

### Features Working
- CV text to structured JSON conversion
- SHA256 hash-based deduplication
- MongoDB Atlas integration
- Automatic index creation
- CV storage and retrieval
- Missing keywords analysis (CV vs Job Description)

---

## Implementation Details

### GeminiService (Port 8002)

**Files Implemented:**
- `gemini_service/app/llm_client.py` - Gemini API integration
- `gemini_service/app/service.py` - Business logic and metadata generation
- `gemini_service/app/api.py` - FastAPI endpoints
- `gemini_service/app/main.py` - Application entry point

**Functionality:**
- Parses raw CV text using Gemini 2.5 Flash model
- Extracts structured sections: contact, education, experience, skills, projects, etc.
- Generates metadata: timestamp, word count, character count, sections detected
- Returns structured JSON with both metadata and structured_sections

**Internal API Endpoints:**
1. `POST /internal/structure_cv` - Takes cv_text, returns structured JSON
2. `POST /internal/missing_keywords` - Takes cv_id and job_description, returns keyword analysis

**New: Missing Keywords Analysis**
- Compares CV against job description using Gemini AI
- Identifies technical and soft skills the candidate HAS
- Identifies technical and soft skills the candidate is MISSING
- Uses semantic matching (e.g., "Spring Boot" matches "Java frameworks")
- Returns cv_id and filename for identification

---

### StoringService (Port 8001)

**Files Implemented:**
- `storing_service/app/db_mongo.py` - MongoDB connection and operations
- `storing_service/app/service.py` - Hash calculation and deduplication logic
- `storing_service/app/api.py` - FastAPI endpoints
- `storing_service/app/main.py` - Application entry point with index creation

**Functionality:**
- Calculates SHA256 hash of CV text as unique identifier
- Checks for duplicates before storing (deduplication)
- Stores CV with metadata and structured sections
- Creates MongoDB indexes automatically on startup
- Retrieves CVs by cv_id

**Internal API Endpoints:**
- `POST /internal/store_cv` - Store CV with deduplication
- `GET /internal/get_cv/{cv_id}` - Retrieve CV by hash

**MongoDB Document Structure:**
```
{
  "cv_id": "sha256_hash",
  "cv_text": "original raw text",
  "metadata": {
    "timestamp": "...",
    "character_count": 3561,
    "word_count": 511,
    "sections_detected": 5,
    "parser_version": "1.0.0",
    "extraction_method": "gemini-2.5-flash"
  },
  "structured_sections": {
    "contact": {...},
    "education": [...],
    "experience": [...],
    "skills": {...},
    ...
  },
  "created_at": "2025-11-19T...",
  "updated_at": "2025-11-19T..."
}
```

---

## Setup and Testing Guide

### Prerequisites

1. Python 3.11+
2. MongoDB Atlas account with connection string
3. Gemini API key

### Step 1: Environment Configuration

**Create `.env` files for each service:**

**gemini_service/.env:**
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**storing_service/.env:**
```
MONGODB_URI=mongodb+srv://cloud:coen424@cluster-coen-424.qvcetbu.mongodb.net/
```

### Step 2: Install Dependencies

**For GeminiService:**
```bash
cd gemini_service
pip install -r requirements.txt
```

**For StoringService:**
```bash
cd storing_service
pip install -r requirements.txt
```

### Step 3: Start the Services

**Terminal 1 - Start GeminiService:**
```bash
cd gemini_service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Application startup complete.
```

**Terminal 2 - Start StoringService:**
```bash
cd storing_service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
Database indexes created successfully
INFO:     Application startup complete.
```

---

## Testing Procedures

### Test 1: CV Structuring with GeminiService

**Access Swagger UI:**
```
http://localhost:8002/docs
```

**Test Endpoint:** `POST /internal/structure_cv`

**Sample Request:**
```json
{
  "cv_text": "Education\n\n(111) 111-1111\n\nErik Cupsa\n\ngithub.com/erik-cupsa\n\nerikcupsa@gmail.com\n\nlinkedin.com/in/erik-cupsa\n\nMcGill University\n\nBachelor of Computer Engineering | Golden Key Honours Scholar\n\nWork Experience\n\nSep 2021- May 2026\n\nGPA: 3.82\n\nAmazon\n\nSoftware Engineer Intern\n\nMay 2025– Aug 2025\n\nToronto, ON\n\n• Owned end-to-end development of a production-grade service using AWS CDK (TypeScript) and Java-based AWS Lambda functions"
}
```

**Expected Response:**
```json
{
  "metadata": {
    "timestamp": "2025-11-19T19:10:36.412562Z",
    "character_count": 3561,
    "word_count": 511,
    "sections_detected": 5,
    "parser_version": "1.0.0",
    "extraction_method": "gemini-2.5-flash"
  },
  "structured_sections": {
    "contact": {
      "name": "Erik Cupsa",
      "email": "erikcupsa@gmail.com",
      ...
    },
    "education": [...],
    "experience": [...],
    "skills": {...}
  }
}
```

**Status:** ✅ Tested and Working

---

### Test 2: CV Storage with StoringService

**Access Swagger UI:**
```
http://localhost:8001/docs
```

**Test Endpoint:** `POST /internal/store_cv`

**Sample Request:**
```json
{
  "structured_json": {
    // Paste the entire response from Test 1
  },
  "cv_text": "Education\n\n(111) 111-1111\n\nErik Cupsa\n..."
}
```

**Expected Response:**
```json
{
  "cv_id": "5fb195e50e7dd41b037b52131883e13ec36a6619fb3208cb80693464be0ca12c",
  "status": "stored",
  "message": "CV stored successfully"
}
```

**Status:** ✅ Tested and Working

---

### Test 3: CV Retrieval

**Test Endpoint:** `GET /internal/get_cv/{cv_id}`

**Procedure:**
1. Copy the cv_id from Test 2 response
2. Navigate to GET endpoint in Swagger UI
3. Paste cv_id in the parameter field
4. Execute

**Expected Response:**
Complete CV document from MongoDB with all fields

**Status:** ✅ Tested and Working

---

### Test 4: Deduplication Verification

**Test Endpoint:** `POST /internal/store_cv`

**Procedure:**
1. Try to store the exact same CV again (same structured_json and cv_text)
2. Execute the request

**Expected Response:**
```json
{
  "cv_id": "5fb195e50e7dd41b037b52131883e13ec36a6619fb3208cb80693464be0ca12c",
  "status": "already_exists",
  "message": "CV with this content already exists"
}
```

**Status:** ✅ Tested and Working (Deduplication prevents duplicate storage)

---

### Test 5: MongoDB Atlas Verification

**Access MongoDB Atlas:**
1. Go to MongoDB Atlas Dashboard
2. Click "Browse Collections"
3. Database: `tailorcv_db`
4. Collection: `cvs`

**Verification Points:**
- ✅ Database `tailorcv_db` created
- ✅ Collection `cvs` created
- ✅ 1 document stored
- ✅ Document contains: cv_id, cv_text, metadata, structured_sections, timestamps
- ✅ Indexes created: unique index on cv_id, descending index on created_at

**Status:** ✅ Verified

---

### Test 6: Missing Keywords Analysis

**Access Swagger UI:**
```
http://localhost:8002/docs
```

**Test Endpoint:** `POST /internal/missing_keywords`

**Prerequisites:**
- Both GeminiService (port 8002) and StoringService (port 8001) must be running
- At least one CV must be stored in MongoDB (use cv_id from Test 2)

**Sample Request:**
```json
{
  "cv_id": "5fb195e50e7dd41b037b52131883e13ec36a6619fb3208cb80693464be0ca12c",
  "job_description": "We are looking for a Backend Software Engineer with expertise in Kubernetes, Go (Golang), Apache Kafka, and microservices architecture. The ideal candidate should have experience with distributed systems, cloud platforms (AWS/GCP), and strong problem-solving skills. Experience with React, GraphQL, and MongoDB is a plus. We value strong communication skills and the ability to work in cross-functional teams."
}
```

**Expected Response:**
```json
{
  "cv_id": "5fb195e50e7dd41b037b52131883e13ec36a6619fb3208cb80693464be0ca12c",
  "filename": "Unknown",
  "keywords_you_have": {
    "technical": [
      "AWS",
      "Microservices",
      "Cloud platforms",
      "MongoDB"
    ],
    "soft": [
      "Problem-solving",
      "Communication",
      "Cross-functional teams"
    ]
  },
  "keywords_missing": {
    "technical": [
      "Kubernetes",
      "Go (Golang)",
      "Apache Kafka",
      "Distributed systems",
      "React",
      "GraphQL"
    ],
    "soft": []
  }
}
```

**What It Does:**
1. Fetches the CV from StoringService using cv_id
2. Extracts structured_sections from the CV
3. Calls Gemini AI to compare CV against job description
4. Uses semantic matching (e.g., "Java" matches "backend development")
5. Categorizes keywords into technical and soft skills
6. Returns what the candidate HAS and what they're MISSING

**Status:** ✅ Ready for Testing

---

## Test Results Summary

| Test | Component | Status | Notes |
|------|-----------|--------|-------|
| CV Structuring | GeminiService | ✅ Pass | Successfully parsed CV text to structured JSON |
| CV Storage | StoringService | ✅ Pass | Stored CV in MongoDB with hash-based cv_id |
| CV Retrieval | StoringService | ✅ Pass | Retrieved complete CV document by cv_id |
| Deduplication | StoringService | ✅ Pass | Prevented duplicate storage of same CV |
| Database Connection | StoringService | ✅ Pass | Connected to MongoDB Atlas successfully |
| Index Creation | StoringService | ✅ Pass | Indexes created automatically on startup |
| Missing Keywords | GeminiService + StoringService | 🔄 Ready | Analyzes CV vs JD for matching/missing keywords |

---

## Architecture Decisions Validated

1. **Hash-based Deduplication:** Successfully prevents duplicate CVs using SHA256 of raw text
2. **Metadata Storage:** Useful analytics preserved (word count, timestamp, etc.)
3. **Structured Sections:** Clean separation of CV data by sections
4. **MongoDB Schema:** Document structure works well for storage and retrieval
5. **Index Strategy:** Unique index on cv_id and descending index on created_at for performance

---

## What's Next (Not Yet Implemented)

### Phase 2: Additional GeminiService Endpoints
- `POST /internal/missing_keywords` - Find missing keywords in CV vs JD
- `POST /internal/score` - Score CV against job description
- `POST /internal/tailored_bullets` - Generate tailored bullet points

### Phase 3: API Gateway Integration
- Public endpoint `/attach_cv` orchestrating GeminiService and StoringService
- Public endpoint `/keywords` for keyword analysis
- Public endpoint `/score` for CV scoring

### Phase 4: VectorService & Async Processing
- Background embedding generation with RabbitMQ
- Pinecone vector database integration
- Semantic similarity search

### Phase 5: Redis Caching
- Cache latest CV for fast retrieval
- Reduce MongoDB query load

---

---

## Notes

- Services must be started in separate terminals
- Both services must be running for full testing
- Swagger UI auto-generated at `/docs` endpoint for each service
- Use `python -m uvicorn` instead of just `uvicorn` on Windows if PATH issues occur
- MongoDB Atlas connection string stored in `.env` file (not committed to git)
- Gemini API key stored in `.env` file (not committed to git)

---

## Team Members

Successfully tested by: [Aman]  
Date: November 19, 2025

---

**End of Implementation Status Report**

