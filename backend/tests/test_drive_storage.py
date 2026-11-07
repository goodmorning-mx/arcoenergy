from __future__ import annotations

import pytest

from app import drive_storage


class FakeResponse:
    def __init__(self, status_code=200, headers=None, payload=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_upload_refuses_non_google_resumable_url(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def request(self, *args, **kwargs):
            return FakeResponse(headers={"Location": "https://attacker.example/session"})

    monkeypatch.setattr(drive_storage, "_access_token", lambda: "secret")
    monkeypatch.setattr(drive_storage, "get_settings", lambda: type("Settings", (), {"google_drive_folder_id": "folder-id"})())
    monkeypatch.setattr(drive_storage.httpx, "Client", FakeClient)
    with pytest.raises(RuntimeError, match="invalid_upload_session"):
        drive_storage.save_quote_pdf(folio="AE-2026-00001", pdf=b"%PDF")


def test_folder_status_reports_unconfigured_without_provider_call(monkeypatch):
    class Settings:
        google_drive_folder_id = ""
        google_drive_service_account_json = ""

    monkeypatch.setattr(drive_storage, "get_settings", lambda: Settings())
    monkeypatch.setattr(drive_storage, "_access_token", lambda: pytest.fail("must not request a token"))
    assert drive_storage.folder_status() == {"connected": False, "status": "folder_not_configured"}


def test_folder_status_requires_an_actual_drive_folder(monkeypatch):
    class Settings:
        google_drive_folder_id = "folder-id"
        google_drive_service_account_json = "configured-secret"

    monkeypatch.setattr(drive_storage, "get_settings", lambda: Settings())
    monkeypatch.setattr(drive_storage, "_access_token", lambda: "secret")
    monkeypatch.setattr(drive_storage.httpx, "get", lambda *args, **kwargs: FakeResponse(payload={"id": "folder-id", "mimeType": "text/plain", "name": "not a folder"}))
    assert drive_storage.folder_status() == {"connected": False, "status": "invalid_folder"}
