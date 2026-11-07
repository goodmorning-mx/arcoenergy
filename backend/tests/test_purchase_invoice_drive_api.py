import asyncio

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app import product_api
from app.models import Purchase

CFDI_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Comprobante xmlns:cfdi="http://www.sat.gob.mx/cfd/4" xmlns:tfd="http://www.sat.gob.mx/TimbreFiscalDigital"
  Version="4.0" TipoDeComprobante="I" Fecha="2026-11-06T12:30:00" Moneda="MXN"
  Serie="AE" Folio="125" SubTotal="100.00" Total="116.00">
  <cfdi:Emisor Rfc="AAA010101AAA" Nombre="Proveedor Solar"/>
  <cfdi:Conceptos><cfdi:Concepto ClaveProdServ="26111600" NoIdentificacion="PANEL-610"
    Cantidad="2" ClaveUnidad="H87" Unidad="Pieza" Descripcion="Panel solar 610 W"
    ValorUnitario="50.00" Importe="100.00"/></cfdi:Conceptos>
  <cfdi:Complemento><tfd:TimbreFiscalDigital UUID="ABCDEF00-1234-5678-9012-ABCDEF000000"/></cfdi:Complemento>
</cfdi:Comprobante>'''


class FakeDb:
    def __init__(self, purchase):
        self.purchase = purchase
        self.committed = False

    def get(self, model, key):
        return self.purchase if model is Purchase and key == self.purchase.id else None

    def commit(self):
        self.committed = True


def make_request(content_type, filename, content):
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


def test_purchase_invoice_pdf_is_saved_and_linked_to_purchase(monkeypatch):
    purchase = Purchase(id="purchase-1", folio="AE-C-2026-00001")
    db = FakeDb(purchase)
    received = {}
    monkeypatch.setattr(product_api, "save_private_file", lambda **kwargs: received.update(kwargs) or "drive-1")
    result = asyncio.run(product_api.upload_purchase_invoice_file(
        "purchase-1", make_request("application/pdf", "factura.pdf", b"%PDF-1.7 invoice"), object(), db,
    ))
    assert result["saved"] is True
    assert received["filename"] == "AE-C-2026-00001-factura.pdf"
    assert purchase.invoice_drive_file_id == "drive-1"
    assert purchase.invoice_filename == "factura.pdf"
    assert db.committed


def test_valid_cfdi_xml_can_be_archived_but_external_entities_are_rejected(monkeypatch):
    purchase = Purchase(id="purchase-1", folio="AE-C-2026-00001")
    db = FakeDb(purchase)
    received = {}
    monkeypatch.setattr(product_api, "save_private_file", lambda **kwargs: received.update(kwargs) or "drive-xml")
    result = asyncio.run(product_api.upload_purchase_invoice_file(
        "purchase-1", make_request("application/xml", "factura.xml", CFDI_XML.encode()), object(), db,
    ))
    assert result["saved"] is True
    assert received["content_type"] == "application/xml"
    assert purchase.invoice_drive_file_id == "drive-xml"

    with pytest.raises(HTTPException) as error:
        asyncio.run(product_api.upload_purchase_invoice_file(
            "purchase-1", make_request("application/xml", "malicious.xml", b"<!DOCTYPE x [<!ENTITY e 'x'>]><x>&e;</x>"), object(), db,
        ))
    assert error.value.status_code == 415


def test_purchase_invoice_rejects_mismatched_file_signatures(monkeypatch):
    purchase = Purchase(id="purchase-1", folio="AE-C-2026-00001")
    monkeypatch.setattr(product_api, "save_private_file", lambda **kwargs: pytest.fail("must reject before Drive upload"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(product_api.upload_purchase_invoice_file(
            "purchase-1", make_request("application/pdf", "factura.pdf", b"not a PDF"), object(), FakeDb(purchase),
        ))
    assert error.value.status_code == 415


def test_purchase_invoice_download_uses_private_drive_proxy(monkeypatch):
    purchase = Purchase(id="purchase-1", folio="AE-C-2026-00001")
    purchase.invoice_drive_file_id = "drive-1"
    purchase.invoice_filename = "factura solar.pdf"
    purchase.invoice_content_type = "application/pdf"
    monkeypatch.setattr(product_api, "download_private_file", lambda file_id: httpx.Response(200, content=b"%PDF"))
    response = product_api.get_purchase_invoice_file("purchase-1", object(), FakeDb(purchase))
    assert response.body == b"%PDF"
    assert response.media_type == "application/pdf"
    assert response.headers["content-disposition"] == "attachment; filename*=UTF-8''factura%20solar.pdf"

