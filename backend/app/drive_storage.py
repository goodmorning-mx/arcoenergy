"""Private Google Drive storage for customer quote documents."""
from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import get_settings

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DRIVE_API = "https://www.googleapis.com/drive/v3"


def _access_token() -> str:
    settings = get_settings()
    if not settings.google_drive_service_account_json or not settings.google_drive_folder_id:
        raise RuntimeError("not_configured")
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    info = json.loads(settings.google_drive_service_account_json)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=[DRIVE_SCOPE])
    credentials.refresh(Request())
    if not credentials.token:
        raise RuntimeError("authentication_failed")
    return credentials.token


def folder_status(settings=None) -> dict[str, Any]:
    settings = settings or get_settings()
    if not settings.google_drive_folder_id:
        return {"connected": False, "status": "folder_not_configured"}
    if not getattr(settings, "google_drive_service_account_json", ""):
        return {"connected": False, "status": "credentials_not_configured"}
    try:
        token = _access_token()
        response = httpx.get(
            f"{DRIVE_API}/files/{settings.google_drive_folder_id}",
            params={"fields": "id,name,mimeType,trashed", "supportsAllDrives": "true"},
            headers={"Authorization": f"Bearer {token}"}, timeout=20,
        )
        if response.status_code != 200:
            return {"connected": False, "status": "folder_access_denied"}
        folder = response.json()
        if folder.get("trashed") or folder.get("mimeType") != "application/vnd.google-apps.folder":
            return {"connected": False, "status": "invalid_folder"}
        return {"connected": True, "status": "connected", "folder_name": folder.get("name", "")}
    except Exception:
        # Do not leak service-account data, OAuth responses, or provider errors.
        return {"connected": False, "status": "connection_check_failed"}


def save_quote_pdf(*, folio: str, pdf: bytes, existing_file_id: str = "") -> str:
    """Save or replace a PDF in the configured private folder; return its Drive id."""
    settings = get_settings()
    token = _access_token()
    headers = {"Authorization": f"Bearer {token}"}
    metadata: dict[str, Any] = {"name": f"{folio}.pdf", "mimeType": "application/pdf"}
    if existing_file_id:
        url = f"{DRIVE_API}/files/{existing_file_id}"
        method = "PATCH"
    else:
        metadata["parents"] = [settings.google_drive_folder_id]
        url = f"{DRIVE_API}/files"
        method = "POST"
    with httpx.Client(timeout=30, follow_redirects=False) as client:
        response = client.request(
            method, url,
            params={"uploadType": "resumable", "fields": "id,name", "supportsAllDrives": "true"},
            headers={**headers, "Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": "application/pdf", "X-Upload-Content-Length": str(len(pdf))},
            json=metadata,
        )
        if response.status_code not in (200, 201):
            raise RuntimeError("upload_session_failed")
        upload_url = response.headers.get("Location", "")
        parsed = httpx.URL(upload_url)
        if parsed.scheme != "https" or parsed.host not in {"www.googleapis.com", "content.googleapis.com"}:
            raise RuntimeError("invalid_upload_session")
        uploaded = client.put(upload_url, content=pdf, headers={**headers, "Content-Type": "application/pdf", "Content-Length": str(len(pdf))})
        if uploaded.status_code not in (200, 201):
            raise RuntimeError("upload_failed")
        result = uploaded.json()
        if not result.get("id"):
            raise RuntimeError("upload_missing_id")
        return str(result["id"])
