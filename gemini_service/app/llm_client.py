import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def initialize_gemini():
    """Initialize Gemini API with API key from environment"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def create_parsing_prompt(cv_text: str) -> str:
    """Create the intelligent parsing prompt for Gemini"""
    return f"""
You are an expert CV parser. Parse this CV and extract ALL information into structured JSON.

IMPORTANT INSTRUCTIONS:

1. NORMALIZE section names (understand semantic equivalents):
   - "Academic Journey", "Academic Background", "Education History" → map to "education"
   - "Technical Skills", "Technical Expertise", "Core Competencies", "Technical Competencies" → map to "skills"
   - "Professional Experience", "Work History", "Career", "Work Experience" → map to "experience"
   - "Side Projects", "Personal Projects" → map to "projects"
   - "Summary", "Objective", "Profile", "Professional Summary" → map to "summary"

2. For SKILLS section, intelligently categorize:
   - Programming languages → "languages" array
   - Frameworks/Libraries → "frameworks" array
   - Cloud platforms (AWS, GCP, Azure, etc.) → "cloud" array (only if mentioned)
   - DevOps tools (Docker, Kubernetes, Jenkins, etc.) → "devops" array (only if mentioned)
   - Databases (PostgreSQL, MongoDB, etc.) → "databases" array (only if mentioned)
   - Development tools → "tools" array
   - Other skills → "other" array

3. EXTRACT technologies from experience bullet points even if not explicitly in skills section

4. OPTIONAL sections (only include if present in CV):
   - certifications
   - publications
   - awards
   - volunteer work
   - languages spoken

5. If you find sections you can't categorize (like "Hobbies", "Volunteer Work", "Languages Spoken"), 
   put them in "additional_sections" with the original section name as key

6. For dates, normalize to "Mon YYYY" format (e.g., "May 2024", "Present")

CV TEXT TO PARSE:
{cv_text}

Return ONLY valid JSON (no markdown, no code blocks, no explanation) with this EXACT structure:
{{
  "contact": {{
    "name": "full name or null",
    "email": "email or null",
    "phone": "phone or null",
    "linkedin": "linkedin url or null",
    "github": "github url or null",
    "website": "website url or null"
  }},
  
  "summary": {{
    "text": "professional summary text or null",
    "key_highlights": []
  }},
  
  "education": [
    {{
      "institution": "university/college name",
      "degree": "degree name or null",
      "field": "field of study or null",
      "start_date": "start date or null",
      "end_date": "end date or null",
      "gpa": "GPA or null",
      "honors": []
    }}
  ],
  
  "experience": [
    {{
      "company": "company name",
      "title": "job title",
      "location": "location or null",
      "start_date": "start date or null",
      "end_date": "end date or 'Present' or null",
      "bullets": ["full bullet point text"],
      "technologies": ["tech extracted from bullets"]
    }}
  ],
  
  "skills": {{
    "languages": [],
    "frameworks": [],
    "cloud": [],
    "devops": [],
    "databases": [],
    "tools": [],
    "other": []
  }},
  
  "certifications": [
    {{
      "name": "certification name",
      "issuer": "issuing organization or null",
      "date": "date obtained or null",
      "credential_id": "credential ID or null"
    }}
  ],
  
  "projects": [
    {{
      "name": "project name",
      "description": "brief description or null",
      "technologies": [],
      "link": "project link or null",
      "start_date": "start date or null",
      "end_date": "end date or null"
    }}
  ],
  
  "leadership": [
    {{
      "role": "leadership role title",
      "organization": "organization name",
      "start_date": "start date or null",
      "end_date": "end date or null",
      "description": "brief description or null"
    }}
  ],
  
  "publications": [
    {{
      "title": "publication title",
      "venue": "conference/journal or null",
      "date": "publication date or null",
      "link": "publication link or null"
    }}
  ],
  
  "awards": [
    {{
      "name": "award name",
      "issuer": "issuing organization or null",
      "date": "date received or null"
    }}
  ],
  
  "additional_sections": {{
  }}
}}

CRITICAL RULES:
1. Return ONLY the JSON object, no markdown formatting, no ```json```, no explanation text
2. Use null for missing single values, [] for missing arrays
3. Empty arrays [] for optional sections not present in CV
4. Extract FULL bullet points exactly as written
5. Be intelligent about semantic equivalents and variations
6. Extract technologies mentioned in experience descriptions
"""

def call_gemini_to_structure_cv(cv_text: str) -> dict:
    """
    Call Gemini API to structure CV text into JSON
    
    Args:
        cv_text: Raw CV text
        
    Returns:
        Dictionary with structured CV sections
    """
    model = initialize_gemini()
    prompt = create_parsing_prompt(cv_text)
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Clean up response (remove markdown if present)
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
    
    # Parse JSON
    structured_data = json.loads(response_text)
    
    # Validate and clean
    validated_data = validate_and_clean(structured_data)
    
    return validated_data

def validate_and_clean(data: dict) -> dict:
    """Validate and clean the Gemini output"""
    required_keys = [
        'contact', 'summary', 'education', 'experience',
        'skills', 'certifications', 'projects', 'leadership',
        'publications', 'awards', 'additional_sections'
    ]
    
    for key in required_keys:
        if key not in data:
            if key in ['education', 'experience', 'certifications', 'projects',
                      'leadership', 'publications', 'awards']:
                data[key] = []
            elif key == 'contact':
                data[key] = {}
            elif key == 'summary':
                data[key] = {"text": None, "key_highlights": []}
            elif key == 'skills':
                data[key] = {
                    "languages": [], "frameworks": [], "cloud": [],
                    "devops": [], "databases": [], "tools": [], "other": []
                }
            elif key == 'additional_sections':
                data[key] = {}
    
    # Ensure skills has all categories
    if 'skills' in data:
        skill_categories = ['languages', 'frameworks', 'cloud', 'devops',
                          'databases', 'tools', 'other']
        for category in skill_categories:
            if category not in data['skills']:
                data['skills'][category] = []
    
    # Remove empty skill categories
    if 'skills' in data:
        data['skills'] = {
            k: v for k, v in data['skills'].items() if v
        }
    
    return data

