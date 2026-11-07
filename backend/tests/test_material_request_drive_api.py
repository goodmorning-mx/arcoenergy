import asyncio

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import product_api
from app.models import Installation


class FakeDb:
    def __init__(self, installation):
        self.installation = installation
        self.committed = False

    def get(self, model, key):
        return self.installation if model is Installation and key == self.installation.id else None

    def commit(self):
        self.committed = True


def request_for(content_type, filename, content):
    headers = [(b"content-type", content_type.encode()), (b"content-length", str(len(content)).encode()),
               (b"x-document-name", filename.encode())]
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.request", "body": b"", "more_body": False}
        delivered = True
        return {"type": "http.request", "body": content, "more_body": False}

    scope = {"type": "http", "method": "PUT", "path": "/", "headers": headers,
             "query_string": b"", "server": ("test", 80), "client": ("test", 1234),
             "scheme": "http", "http_version": "1.1"}
    return Request(scope, receive)


def test_material_request_is_uploaded_and_linked_to_installation(monkeypatch):
    installation = Installation(id="install-1", folio="AE-1")
    db = FakeDb(installation)
    saved = {}

    def save(**kwargs):
        saved.update(kwargs)
        return "drive-file-1"

    monkeypatch.setattr(product_api, "save_private_file", save)
    result = asyncio.run(product_api.upload_material_request_file(
        "install-1", request_for("application/pdf", "orden.pdf", b"%PDF-1.7 content"), object(), db,
    ))
    assert result["saved"] is True
    assert saved["filename"] == "orden-AE-1-orden.pdf"
    assert installation.material_request_drive_file_id == "drive-file-1"
    assert installation.material_request_filename == "orden.pdf"
    assert db.committed


def test_material_request_requires_matching_file_signature(monkeypatch):
    installation = Installation(id="install-1", folio="AE-1")
    monkeypatch.setattr(product_api, "save_private_file", lambda **kwargs: pytest.fail("must reject before upload"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(product_api.upload_material_request_file(
            "install-1", request_for("application/pdf", "orden.pdf", b"not a PDF"), object(), FakeDb(installation),
        ))
    assert error.value.status_code == 415


def test_material_request_reports_drive_not_configured_without_claiming_archive(monkeypatch):
    installation = Installation(id="install-1", folio="AE-1")
    db = FakeDb(installation)
    monkeypatch.setattr(product_api, "save_private_file", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("not_configured")))
    with pytest.raises(HTTPException) as error:
        asyncio.run(product_api.upload_material_request_file(
            "install-1", request_for("application/pdf", "orden.pdf", b"%PDF-1.7 content"), object(), db,
        ))
    assert error.value.status_code == 503
    assert error.value.detail == "drive_not_configured"
    assert not db.committed


def test_material_request_download_is_private_and_uses_safe_filename(monkeypatch):
    installation = Installation(id="install-1", folio="AE-1")
    installation.material_request_drive_file_id = "private-id"
    installation.material_request_filename = "orden solar.pdf"
    installation.material_request_content_type = "application/pdf"
    monkeypatch.setattr(product_api, "download_private_file", lambda file_id: httpx.Response(200, content=b"%PDF"))
    response = product_api.get_material_request_file("install-1", object(), FakeDb(installation))
    assert response.body == b"%PDF"
    assert response.media_type == "application/pdf"
    assert response.headers["content-disposition"] == "attachment; filename*=UTF-8''orden%20solar.pdf"

