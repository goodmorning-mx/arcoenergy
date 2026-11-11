import asyncio

from fastapi import HTTPException
from starlette.requests import Request

from app import product_api


def make_request(raw: bytes, *, content_type: str = "application/pdf", filename: str = "orden.pdf") -> Request:
    async def receive():
        return {"type": "http.request", "body": raw, "more_body": False}

    return Request({
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "POST", "scheme": "https", "path": "/v1/inventory/read-material-request",
        "raw_path": b"/v1/inventory/read-material-request", "query_string": b"",
        "headers": [
            (b"content-type", content_type.encode()),
            (b"content-length", str(len(raw)).encode()),
            (b"x-document-name", filename.encode()),
        ],
        "server": ("test", 443), "client": ("127.0.0.1", 1234),
    }, receive)


def test_material_request_read_returns_transient_review_text_without_inventory_write(monkeypatch):
    calls = []
    monkeypatch.setattr(product_api, "_extract_purchase_invoice_text", lambda content, content_type: calls.append((content, content_type)) or ("Panel fotovoltaico 4\nInversor 1", "ocr"))
    result = asyncio.run(product_api.read_material_request_document(make_request(b"%PDF-1.7 sample", filename="../solicitud.pdf")))

    assert result == {
        "filename": "solicitud.pdf",
        "extraction_method": "ocr",
        "extracted_text": "Panel fotovoltaico 4\nInversor 1",
        "review_only": True,
        "source_stored": False,
        "inventory_changed": False,
    }
    assert calls == [(b"%PDF-1.7 sample", "application/pdf")]


def test_material_request_read_rejects_content_with_wrong_signature(monkeypatch):
    monkeypatch.setattr(product_api, "_extract_purchase_invoice_text", lambda *_: (_ for _ in ()).throw(AssertionError("OCR must not run")))
    try:
        asyncio.run(product_api.read_material_request_document(make_request(b"not a PDF")))
    except HTTPException as error:
        assert error.status_code == 415
    else:
        raise AssertionError("Expected invalid PDF signature to be rejected")


def test_material_request_ocr_route_requires_inventory_issue_permission():
    route = next(route for route in product_api.router.routes if getattr(route, "path", "") == "/v1/inventory/read-material-request")
    assert len(route.dependencies) == 1
    guard = route.dependencies[0].dependency
    closure = dict(zip(guard.__code__.co_freevars, (cell.cell_contents for cell in guard.__closure__)))
    assert closure["required"] == ("inventory:issue",)
