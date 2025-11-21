# HTTP Client for StoringService
# Makes HTTP requests to StoringService internal APIs
#
# Internal API calls:
# - StoreCV(structured_json_cv, cv_text) -> cv_id
# - getCV(cv_id) -> structured_json
# - getLatestCV() -> structured_json
#
# Responsibilities:
# - Build HTTP requests to StoringService endpoints
# - Handle connection errors and retries
# - Parse responses

import os
from typing import Any, Dict

import httpx

STORING_SERVICE_URL = os.getenv("STORING_SERVICE_URL", "http://localhost:8001")


class StoringClientError(Exception):
    """Custom exception for StoringService errors."""


async def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{STORING_SERVICE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise StoringClientError(f"Error connecting to StoringService: {exc}") from exc

    if resp.status_code >= 400:
        raise StoringClientError(
            f"StoringService returned {resp.status_code}: {resp.text}"
        )
    return resp.json()


async def _get(path: str) -> Dict[str, Any]:
    url = f"{STORING_SERVICE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
    except httpx.RequestError as exc:
        raise StoringClientError(f"Error connecting to StoringService: {exc}") from exc

    if resp.status_code >= 400:
        raise StoringClientError(
            f"StoringService returned {resp.status_code}: {resp.text}"
        )
    return resp.json()


async def store_cv(structured_cv: Dict[str, Any], cv_text: str, user_id: str) -> Dict[str, Any]:
    """
    Store CV (structured json + raw text).
    Internal endpoint: POST /internal/store_cv
    """
    payload = {"user_id": user_id, "structured_cv": structured_cv, "cv_text": cv_text}
    return await _post("/internal/store_cv", payload)


async def get_cv(cv_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific CV by id.
    Internal endpoint: GET /internal/get_cv/{cv_id}
    """
    return await _get(f"/internal/get_cv/{cv_id}")


async def get_latest_cv(user_id: str | None = None) -> Dict[str, Any]:
    """
    Retrieve the latest CV; optionally per user if your backend supports it.
    Internal endpoint: GET /internal/get_latest_cv or /internal/get_latest_cv?user_id=...
    """
    if user_id:
        return await _get(f"/internal/get_latest_cv?user_id={user_id}")
    return await _get("/internal/get_latest_cv")