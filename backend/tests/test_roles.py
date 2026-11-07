from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Customer, Installation, Quote, Receivable
from app.roles import ROLE_LABELS, ROLE_PERMISSIONS, canonical_role
from app.product_api import client_portal_data, team_roles
from gm_auth.models import AuthIdentity


def test_role_catalog_contains_exact_requested_roles_and_scopes() -> None:
    assert set(ROLE_LABELS) == {"contador", "marketing", "administrador", "instalador", "cliente"}
    assert "team:manage" in ROLE_PERMISSIONS["administrador"]
    assert "receivables:write" in ROLE_PERMISSIONS["contador"]
    assert {"sales:read", "sales:write"} <= ROLE_PERMISSIONS["administrador"]
    assert {"sales:read", "sales:write"} <= ROLE_PERMISSIONS["contador"]
    assert "reports:read" in ROLE_PERMISSIONS["administrador"]
    assert "reports:read" in ROLE_PERMISSIONS["contador"]
    assert "reports:read" not in ROLE_PERMISSIONS["marketing"]
    assert "quotes:write" in ROLE_PERMISSIONS["marketing"]
    assert "inventory:write" in ROLE_PERMISSIONS["instalador"]
    assert "inventory:issue" not in ROLE_PERMISSIONS["instalador"]
    assert "inventory:issue" in ROLE_PERMISSIONS["administrador"]
    assert "inventory:issue" in ROLE_PERMISSIONS["contador"]
    assert "inventory:issue" not in ROLE_PERMISSIONS["marketing"]
    assert "inventory:issue" not in ROLE_PERMISSIONS["cliente"]
    assert "inventory:costs:read" not in ROLE_PERMISSIONS["instalador"]
    assert ROLE_PERMISSIONS["cliente"] == frozenset({"client:portal"})
    assert "customers:read" not in ROLE_PERMISSIONS["cliente"]
    assert canonical_role(" admin ") == "administrador"
    assert canonical_role("ventas") == "marketing"
    assert canonical_role("finanzas") == "contador"


def test_roles_that_record_inventory_usage_cannot_read_direct_costs() -> None:
    assert "inventory:write" in ROLE_PERMISSIONS["instalador"]
    assert "inventory:costs:read" not in ROLE_PERMISSIONS["instalador"]
    assert "expenses:write" in ROLE_PERMISSIONS["instalador"]
    assert "expenses:read" not in ROLE_PERMISSIONS["instalador"]


def test_role_permission_catalog_matches_the_api_matrix() -> None:
    catalog = team_roles()
    assert {row["id"] for row in catalog} == set(ROLE_LABELS)
    for row in catalog:
        assert row["label"] == ROLE_LABELS[row["id"]]
        assert set(row["permissions"]) == ROLE_PERMISSIONS[row["id"]]


def test_client_portal_only_returns_records_for_authenticated_email() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        own = Customer(name="Rosa", email="rosa@example.com", city="Tampico")
        other = Customer(name="Carlos", email="carlos@example.com", city="Altamira")
        db.add_all([own, other]); db.flush()
        db.add_all([
            Quote(folio="AE-1", customer_id=own.id, panel_count=8, panel_brand="Jinko", panel_watts=610, inverter="Growatt 5 kW", payment_method="Contado", panel_subtotal=106000, structure_cost=14900, inverter_cost=22900, total=143800),
            Quote(folio="AE-2", customer_id=other.id, panel_count=12, panel_brand="Jinko", panel_watts=610, inverter="Huawei 6 kW", payment_method="Contado", panel_subtotal=159000, structure_cost=14900, inverter_cost=31900, total=205800),
            Installation(customer_id=own.id, status="assigned", checklist=[]),
            Installation(customer_id=other.id, status="assigned", checklist=[]),
            Receivable(customer_id=own.id, due_date=date(2026, 12, 1), amount=1000, paid_amount=250),
            Receivable(customer_id=other.id, due_date=date(2026, 12, 1), amount=9000, paid_amount=0),
        ]); db.commit()
        payload = client_portal_data(AuthIdentity("rosa-user", "arcoenergy", frozenset({"cliente"}), frozenset({"client:portal"}), "ROSA@example.com", "Rosa"), db)

    assert [row["name"] for row in payload["customers"]] == ["Rosa"]
    assert [row["folio"] for row in payload["quotes"]] == ["AE-1"]
    assert len(payload["installations"]) == 1
    assert payload["payments"][0]["balance"] == 750
    assert payload["payments"][0]["amount"] == 1000
