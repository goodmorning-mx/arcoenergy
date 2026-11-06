from types import SimpleNamespace
import asyncio

import pytest
from fastapi import HTTPException
from gm_mcp import RequestContext, ToolCall

from app import product_api
from app.product_api import QuoteStatusInput, _agent_registry, update_quote_status


class FakeSession:
    def __init__(self, quote):
        self.quote = quote
        self.committed = False

    def get(self, _model, _quote_id):
        return self.quote

    def add(self, _row):
        raise AssertionError("demo status changes must not create activity")

    def commit(self):
        self.committed = True


def test_demo_quote_cannot_be_advanced_to_commercial_status() -> None:
    quote = SimpleNamespace(is_demo=True)
    session = FakeSession(quote)

    with pytest.raises(HTTPException) as error:
        update_quote_status("quote-1", QuoteStatusInput(status="sent"), SimpleNamespace(email="admin@example.test"), session)

    assert error.value.status_code == 409
    assert not session.committed


def test_public_agent_registry_exposes_read_only_catalog_tool_only() -> None:
    tools = _agent_registry("public").list()

    assert [tool["name"] for tool in tools] == ["arcoenergy.public_system_sizes"]
    assert tools[0]["metadata"]["readOnly"] is True
    assert tools[0]["metadata"]["requiresConfirmation"] is False


@pytest.mark.parametrize("approved", [False, True])
def test_public_agent_quotes_only_from_approved_package(monkeypatch, approved: bool) -> None:
    package = SimpleNamespace(
        panel_count=8, panel_brand="DemoSolar", panel_watts=600,
        panel_unit_price=1000, structure_price=2000, structure_name="Estructura demo",
        inverter_options=[{"name": "Inversor 5 kW", "price_mxn": 3000}],
        default_inverter="Inversor 5 kW", payment_methods=["Contado"], enabled=True, is_demo=not approved,
    )

    class PackageRows:
        def all(self):
            return [package]

    class FakeCatalogSession:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def scalars(self, _query):
            return PackageRows()

    monkeypatch.setattr(product_api, "SessionLocal", FakeCatalogSession)
    registry = _agent_registry("public")
    context = RequestContext("public:test", "arcoenergy", "arcoenergy", frozenset({"read"}))
    result = asyncio.run(registry.invoke(ToolCall("arcoenergy.public_system_sizes", {"panel_count": 8}), context)).content

    if approved:
        assert result["quote"]["total_mxn"] == "13000"
        assert result["quote"]["inverter"] == "Inversor 5 kW"
    else:
        assert result["quote"] is None
        assert "total_mxn" not in result
