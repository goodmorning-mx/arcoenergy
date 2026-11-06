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
