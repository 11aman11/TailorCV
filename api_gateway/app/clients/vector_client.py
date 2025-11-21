# HTTP Client for VectorService
# Makes HTTP requests to VectorService internal APIs
#
# Internal API calls:
# - similar-chunks(jd_text) -> list of chunks with metadata
# - search-top-k-cvs(jd_text, top_k) -> list of {cv_id, score}
#
# Responsibilities:
# - Build HTTP requests to VectorService endpoints
# - Handle connection errors and retries
# - Parse responses

import os
from typing import Any, Dict, List

import httpx

VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8003")


class VectorClientError(Exception):
    """Custom exception for VectorService errors."""


async def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{VECTOR_SERVICE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise VectorClientError(f"Error connecting to VectorService: {exc}") from exc

    if resp.status_code >= 400:
        raise VectorClientError(
            f"VectorService returned {resp.status_code}: {resp.text}"
        )
    return resp.json()


async def similar_chunks(jd_text: str) -> Dict[str, Any]:
    """
    Find similar chunks for the given job description.
    Internal endpoint: POST /internal/similar_chunks
    """
    payload = {"jd_text": jd_text}
    return await _post("/internal/similar_chunks", payload)


async def search_top_k_cvs(jd_text: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Search top-k similar CVs for the given job description.
    Internal endpoint: POST /internal/search_top_k_cvs
    """
    payload = {"jd_text": jd_text, "top_k": top_k}
    return await _post("/internal/search_top_k_cvs", payload)