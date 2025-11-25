# TailorCV Frontend

Clean, modern web interface for the TailorCV CV Analysis Platform.

## Features

✅ **CV Upload**
- Upload as text (paste directly)
- Upload as PDF file (automatic text extraction)

✅ **CV Selection**
- Dropdown to select from multiple uploaded CVs
- Auto-loads all CVs from database

✅ **Keyword Analysis**
- Find matching keywords
- Identify missing keywords
- Categorized by technical and soft skills

✅ **CV Scoring**
- Overall score (0-100)
- Category breakdowns (Job Match, Experience, Content, ATS)
- Strengths, gaps, and recommendations

✅ **Clean UI**
- Modern, responsive design
- Loading indicators
- Clear results display
- Mobile-friendly

## Setup

### 1. Start Backend Services

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

### 2. Open Frontend

Simply open `index.html` in your browser:
- Double-click the file, or
- Right-click → Open with → Chrome/Firefox/Edge

**Or serve with Python:**
```bash
cd frontend
python -m http.server 3000
```
Then visit: `http://localhost:3000`

## Usage

### Upload a CV

**Option 1: Text**
1. Click "Paste Text" tab
2. Paste your CV text
3. Click "Upload CV (Text)"
4. Wait for confirmation

**Option 2: PDF**
1. Click "Upload PDF" tab
2. Choose PDF file
3. Click "Upload CV (PDF)"
4. Wait for confirmation

### Analyze CV

1. **Select CV** from dropdown (auto-loads after upload)
2. **Paste Job Description** in text area
3. Click **"Find Keywords"** or **"Get Score"**
4. Wait for AI analysis (~1 minute)
5. View results

## API Configuration

The frontend connects to API Gateway at:
```javascript
const API_BASE_URL = "http://localhost:8000/api";
```

To change the backend URL, edit `app.js` line 6.

## Browser Compatibility

- Chrome/Edge: ✅ Fully supported
- Firefox: ✅ Fully supported
- Safari: ✅ Fully supported
- Mobile browsers: ✅ Responsive design

## Troubleshooting

**CVs not loading?**
- Ensure StoringService is running on port 8001
- Check MongoDB connection
- Check browser console for errors

**Upload fails?**
- Ensure GeminiService is running on port 8002
- Check GEMINI_API_KEY in .env
- Ensure API Gateway is running on port 8000

**CORS errors?**
- API Gateway has CORS enabled by default
- If issues persist, check browser console

## Tech Stack

- **HTML5** - Semantic markup
- **CSS3** - Modern styling, flexbox, animations
- **Vanilla JavaScript** - No frameworks, lightweight
- **Fetch API** - HTTP requests

