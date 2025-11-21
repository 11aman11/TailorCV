# HTTP Client for GeminiService
# Makes HTTP requests to GeminiService internal APIs
#
# Internal API calls:
# - structure-cv(cv_text) -> structured_json_cv
# - missing-keywords(jd_text, cv_id) -> missing_keywords
# - score(jd_text, cv_id) -> score + explanation
# - tailored-bullets(jd_text, chunks) -> bullet_points
#
# Responsibilities:
# - Build HTTP requests to GeminiService endpoints
# - Handle connection errors and retries
# - Parse responses

import os
from typing import Any, Dict, List

import httpx

GEMINI_SERVICE_URL = os.getenv("GEMINI_SERVICE_URL", "http://localhost:8002")


class GeminiClientError(Exception):
    """Custom exception for GeminiService errors."""


async def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{GEMINI_SERVICE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise GeminiClientError(f"Error connecting to GeminiService: {exc}") from exc

    if resp.status_code >= 400:
        raise GeminiClientError(
            f"GeminiService returned {resp.status_code}: {resp.text}"
        )
    return resp.json()


async def structure_cv(cv_text: str) -> Dict[str, Any]:
    """
    Call GeminiService to structure a CV into a JSON schema.
    Internal endpoint: POST /internal/structure_cv
    """
    payload = {"cv_text": cv_text}
    return await _post("/internal/structure_cv", payload)


async def missing_keywords(jd_text: str, cv_id: str) -> Dict[str, Any]:
    """
    Call GeminiService to get missing keywords for a CV vs job description.
    Internal endpoint: POST /internal/missing_keywords
    """
    payload = {"jd_text": jd_text, "cv_id": cv_id}
    return await _post("/internal/missing_keywords", payload)


async def score(jd_text: str, cv_id: str) -> Dict[str, Any]:
    """
    Call GeminiService to get score + explanation for CV vs JD.
    Internal endpoint: POST /internal/score
    """
    payload = {"jd_text": jd_text, "cv_id": cv_id}
    return await _post("/internal/score", payload)


async def tailored_bullets(jd_text: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Call GeminiService to generate tailored bullet points.
    Internal endpoint: POST /internal/tailored_bullets
    """
    payload = {"jd_text": jd_text, "chunks": chunks}
    return await _post("/internal/tailored_bullets", payload)