# TailorCV - Quick Start Guide

Complete setup guide to test the TailorCV platform with UI.

## 🎯 What's Implemented

✅ **GeminiService** (Port 8002)
- Structure CV
- Find missing keywords
- Calculate CV score

✅ **StoringService** (Port 8001)
- Store CVs in MongoDB
- Retrieve CVs
- List all CVs

✅ **API Gateway** (Port 8000)
- Upload CV (text or PDF)
- Get keywords analysis
- Get CV score
- List CVs

✅ **Frontend** (Browser)
- Clean, modern UI
- CV upload (text/PDF)
- CV selection dropdown
- Keyword analysis
- CV scoring

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies

**API Gateway:**
```bash
cd api_gateway
pip install -r requirements.txt
cd ..
```

**All Services:**
```bash
# Gemini and Storing already have dependencies installed
```

### Step 2: Configure Environment

Copy `.env.example` to `.env` and add your API keys:

```bash
cp env.example .env
```

Edit `.env` and add:
```env
# Required
GEMINI_API_KEY_STRUCTURE=your_structure_key_here
GEMINI_API_KEY_KEYWORDS=your_keywords_key_here
GEMINI_API_KEY_SCORE=your_score_key_here
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Optional (use defaults)
STORING_SERVICE_URL=http://localhost:8001
GEMINI_SERVICE_URL=http://localhost:8002
```

### Step 3: Start All Services

**Terminal 1 - StoringService:**
```bash
cd storing_service
python -m uvicorn app.main:app --reload --port 8001
```

**Terminal 2 - GeminiService:**
```bash
cd gemini_service
python -m uvicorn app.main:app --reload --port 8002
```

**Terminal 3 - API Gateway:**
```bash
cd api_gateway
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 4 - Frontend (Optional):**
```bash
cd frontend
python -m http.server 3000
```
Or just open `frontend/index.html` in your browser!

### Step 4: Test It!

Open `frontend/index.html` in your browser and:

1. **Upload a CV** (text or PDF)
2. **Select CV** from dropdown
3. **Paste job description**
4. Click **"Find Keywords"** or **"Get Score"**
5. See results!

---

## 📊 Testing Flow

### Test 1: Upload CV

1. Open frontend
2. Click "Paste Text" tab
3. Paste Erik's CV (already in database) or new CV
4. Click "Upload CV"
5. ✅ See success message with CV ID

### Test 2: Select CV

1. Dropdown automatically loads CVs
2. Select "erik_cupsa.pdf" or your uploaded CV
3. ✅ See selected CV info below dropdown

### Test 3: Find Keywords

1. Paste this job description:
```
We need a Backend Engineer with Python, Java, AWS, and Kubernetes experience.
Must have strong communication skills and leadership abilities.
```

2. Click "Find Keywords"
3. Wait ~1 minute
4. ✅ See keywords you HAVE (green pills)
5. ✅ See keywords you're MISSING (yellow pills)

### Test 4: Get Score

1. Same job description
2. Click "Get Score"
3. Wait ~1 minute
4. ✅ See overall score (e.g., 72/100)
5. ✅ See category breakdowns
6. ✅ See strengths, gaps, recommendations

---

## 🔍 API Endpoints

### Public Endpoints (API Gateway)

```
http://localhost:8000/docs
```

**Available:**
- `GET /api/my_cvs` - List all CVs
- `POST /api/upload_cv_text` - Upload CV as text
- `POST /api/upload_cv_pdf` - Upload CV as PDF
- `POST /api/keywords` - Get missing keywords
- `POST /api/score` - Get CV score

### Internal Endpoints (For Reference)

**StoringService:**
```
http://localhost:8001/docs
```

**GeminiService:**
```
http://localhost:8002/docs
```

---

## 🎨 Frontend Features

### CV Upload
- ✅ Text input (paste directly)
- ✅ PDF upload (automatic extraction)
- ✅ Loading indicators
- ✅ Success/error messages

### CV Selection
- ✅ Dropdown with all CVs
- ✅ Shows filename and CV ID
- ✅ Auto-refresh button

### Keyword Analysis
- ✅ Green pills for keywords you HAVE
- ✅ Yellow pills for keywords you're MISSING
- ✅ Categorized (technical vs soft skills)

### CV Scoring
- ✅ Circular score display (0-100)
- ✅ Rating tier (Excellent, Good, Decent, Fair, Poor)
- ✅ Category breakdowns with progress bars
- ✅ Strengths, gaps, and recommendations

---

## 🐛 Troubleshooting

### Frontend Not Loading CVs?

**Check:**
1. Is StoringService running? (`http://localhost:8001/health`)
2. Is API Gateway running? (`http://localhost:8000/health`)
3. MongoDB connection working?

**Fix:**
```bash
# Check StoringService logs
# Ensure MongoDB URI is correct in .env
```

### Keywords/Score Taking Too Long?

**Normal:** 1-2 minutes for free tier Gemini API

**If longer:**
1. Check Gemini API key is valid
2. Check rate limits (10 req/min per key)
3. Check GeminiService logs

### CORS Errors in Browser?

**Fix:**
API Gateway already has CORS enabled. If issues persist:
```python
# In api_gateway/app/main.py, allow_origins is set to ["*"]
```

### PDF Upload Not Working?

**Check:**
```bash
pip install PyPDF2==3.0.1
```

---

## 📦 What You Can Test Right Now

✅ **Upload CVs** (text or PDF)
✅ **Select CVs** from dropdown
✅ **Keyword Analysis** (with AI)
✅ **CV Scoring** (with AI)
✅ **MongoDB Storage** (automatic)
✅ **Deduplication** (hash-based)
✅ **Clean UI** (responsive)

---

## 🚧 What's Next (Future Implementation)

⏳ **RabbitMQ** - Async embedding
⏳ **VectorService** - Semantic search
⏳ **Redis** - Caching
⏳ **Similar CVs** endpoint
⏳ **Tailored Bullet Points** endpoint

---

## 🎉 You're All Set!

Open `frontend/index.html` and start analyzing CVs! 🚀

**Questions?**
- Check logs in each terminal
- Visit Swagger docs: `http://localhost:8000/docs`
- MongoDB Atlas: Check data in `tailorcv_db.cvs` collection

