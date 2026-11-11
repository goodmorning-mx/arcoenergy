import pytest
from fastapi import HTTPException

from app.product_api import _parse_purchase_cfdi_xml


CFDI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital"
  Version="4.0" TipoDeComprobante="I" Fecha="2026-11-06T12:30:00" Moneda="MXN"
  Serie="AE" Folio="125" SubTotal="100.00" Total="116.00">
  <cfdi:Emisor Rfc="AAA010101AAA" Nombre="Proveedor Solar"/>
  <cfdi:Conceptos><cfdi:Concepto ClaveProdServ="26111600" NoIdentificacion="PANEL-610"
    Cantidad="2" ClaveUnidad="H87" Unidad="Pieza" Descripcion="Panel solar 610 W"
    ValorUnitario="50.00" Importe="100.00"/></cfdi:Conceptos>
  <cfdi:Complemento><tfd:TimbreFiscalDigital UUID="ABCDEF00-1234-5678-9012-ABCDEF000000"/></cfdi:Complemento>
</cfdi:Comprobante>"""


def test_cfdi_parser_returns_a_review_proposal_without_mutating_purchase_data() -> None:
    proposal = _parse_purchase_cfdi_xml(CFDI_XML)

    assert proposal["invoice_reference"] == "ABCDEF00-1234-5678-9012-ABCDEF000000"
    assert proposal["purchase_date"] == "2026-11-06"
    assert proposal["supplier_rfc"] == "AAA010101AAA"
    assert proposal["declared_subtotal"] == 100
    assert proposal["declared_total"] == 116
    assert proposal["concepts"] == [{
        "identifier": "PANEL-610",
        "product_service_key": "26111600",
        "description": "Panel solar 610 W",
        "quantity": 2,
        "unit": "Pieza",
        "net_line_amount": 100,
        "unit_cost_before_global_adjustments": 50,
    }]
    assert proposal["review_only"] is True
    assert proposal["source_xml_stored"] is False
    assert proposal["requires_accounting_review"] is True


@pytest.mark.parametrize("xml, message", [
    ("<Comprobante>", "no contiene un XML CFDI válido"),
    ("<!DOCTYPE a [<!ENTITY x 'bad'>]><Comprobante/>", "no debe declarar DTD"),
    (CFDI_XML.replace('TipoDeComprobante="I"', 'TipoDeComprobante="E"'), "Solo se admiten CFDI de ingreso"),
    (CFDI_XML.replace('Moneda="MXN"', 'Moneda="USD"'), "solo se puede prellenar con facturas en MXN"),
    (CFDI_XML.replace('Cantidad="2"', 'Cantidad="0"'), "cantidad no válida"),
])
def test_cfdi_parser_rejects_unsupported_or_invalid_xml(xml: str, message: str) -> None:
    with pytest.raises(HTTPException) as error:
        _parse_purchase_cfdi_xml(xml)

    assert error.value.status_code == 422
    assert message in str(error.value.detail)


def test_cfdi_parser_enforces_size_limit() -> None:
    with pytest.raises(HTTPException) as error:
        _parse_purchase_cfdi_xml(" " * (2 * 1024 * 1024 + 1))

    assert error.value.status_code == 413


def test_purchase_invoice_pdf_text_extraction_is_transient_and_review_only(monkeypatch) -> None:
    import asyncio
    from starlette.requests import Request

    from app import product_api

    raw = b"%PDF-1.7 fake invoice bytes"
    monkeypatch.setattr(product_api, "_extract_purchase_invoice_text", lambda content, content_type: ("Factura\nTotal: 123.00", "texto_pdf"))

    async def run():
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "https", "path": "/v1/purchases/read-invoice-document",
            "raw_path": b"/v1/purchases/read-invoice-document", "query_string": b"",
            "headers": [(b"content-type", b"application/pdf"), (b"content-length", str(len(raw)).encode()), (b"x-document-name", b"../factura.pdf")],
            "server": ("test", 443), "client": ("127.0.0.1", 1234),
        }
        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}
        return await product_api.read_purchase_invoice_document(Request(scope, receive))

    result = asyncio.run(run())
    assert result == {
        "filename": "factura.pdf",
        "extraction_method": "texto_pdf",
        "extracted_text": "Factura\nTotal: 123.00",
        "review_only": True,
        "source_stored": False,
        "purchase_created": False,
    }


def test_purchase_invoice_document_rejects_mismatched_file_bytes(monkeypatch) -> None:
    import asyncio
    from starlette.requests import Request
    from fastapi import HTTPException

    from app import product_api

    raw = b"not a pdf"
    monkeypatch.setattr(product_api, "_extract_purchase_invoice_text", lambda *_: pytest.fail("OCR must not run for invalid file bytes"))

    async def run():
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "https", "path": "/v1/purchases/read-invoice-document",
            "raw_path": b"/v1/purchases/read-invoice-document", "query_string": b"",
            "headers": [(b"content-type", b"application/pdf"), (b"content-length", str(len(raw)).encode())],
            "server": ("test", 443), "client": ("127.0.0.1", 1234),
        }
        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}
        return await product_api.read_purchase_invoice_document(Request(scope, receive))

    with pytest.raises(HTTPException) as error:
        asyncio.run(run())
    assert error.value.status_code == 415


def test_purchase_invoice_pdf_text_is_read_without_ocr(monkeypatch) -> None:
    from io import BytesIO
    from reportlab.pdfgen import canvas
    from app.product_api import _extract_purchase_invoice_text

    source = BytesIO()
    pdf = canvas.Canvas(source)
    pdf.drawString(72, 720, "Factura solar proveedor Arco Energy - total de compra 1250.00 pesos mexicanos")
    pdf.save()
    text, method = _extract_purchase_invoice_text(source.getvalue(), "application/pdf")

    assert method == "texto_pdf"
    assert "Factura solar" in text
    assert "1250.00" in text


def test_purchase_invoice_photo_ocr_uses_spanish_and_english_and_returns_text(monkeypatch) -> None:
    import sys
    from io import BytesIO
    from types import SimpleNamespace
    from PIL import Image
    from app.product_api import _extract_purchase_invoice_text

    calls = []
    fake_ocr = SimpleNamespace(
        image_to_string=lambda image, **kwargs: calls.append(kwargs) or "Factura\nTotal 1250.00",
        TesseractNotFoundError=type("TesseractNotFoundError", (Exception,), {}),
        TesseractError=type("TesseractError", (Exception,), {}),
    )
    monkeypatch.setitem(sys.modules, "pytesseract", fake_ocr)
    source = BytesIO()
    Image.new("RGB", (120, 80), "white").save(source, format="JPEG")
    text, method = _extract_purchase_invoice_text(source.getvalue(), "image/jpeg")

    assert method == "ocr"
    assert text == "Factura\nTotal 1250.00"
    assert calls == [{"lang": "spa+eng", "config": "--psm 6", "timeout": 12}]


def test_purchase_invoice_document_returns_review_only_and_does_not_store_source(monkeypatch) -> None:
    import asyncio
    from starlette.requests import Request
    from app import product_api

    raw = b"%PDF-1.7 fake invoice bytes"
    monkeypatch.setattr(product_api, "_extract_purchase_invoice_text", lambda content, content_type: ("Factura\nTotal: 123.00", "texto_pdf"))

    async def run():
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "https", "path": "/v1/purchases/read-invoice-document",
            "raw_path": b"/v1/purchases/read-invoice-document", "query_string": b"",
            "headers": [(b"content-type", b"application/pdf"), (b"content-length", str(len(raw)).encode()), (b"x-document-name", b"../factura.pdf")],
            "server": ("test", 443), "client": ("127.0.0.1", 1234),
        }
        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}
        return await product_api.read_purchase_invoice_document(Request(scope, receive))

    result = asyncio.run(run())
    assert result == {
        "filename": "factura.pdf",
        "extraction_method": "texto_pdf",
        "extracted_text": "Factura\nTotal: 123.00",
        "review_only": True,
        "source_stored": False,
        "purchase_created": False,
    }


def test_purchase_invoice_document_rejects_mismatched_file_bytes(monkeypatch) -> None:
    import asyncio
    from starlette.requests import Request
    from app import product_api

    raw = b"not a pdf"
    monkeypatch.setattr(product_api, "_extract_purchase_invoice_text", lambda *_: pytest.fail("OCR must not run for invalid file bytes"))

    async def run():
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "https", "path": "/v1/purchases/read-invoice-document",
            "raw_path": b"/v1/purchases/read-invoice-document", "query_string": b"",
            "headers": [(b"content-type", b"application/pdf"), (b"content-length", str(len(raw)).encode())],
            "server": ("test", 443), "client": ("127.0.0.1", 1234),
        }
        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}
        return await product_api.read_purchase_invoice_document(Request(scope, receive))

    with pytest.raises(HTTPException) as error:
        asyncio.run(run())
    assert error.value.status_code == 415
