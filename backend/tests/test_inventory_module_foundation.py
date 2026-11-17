from decimal import Decimal
from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InventoryCategory, InventoryItem, InventoryMovement, Supplier, WorkOrderMaterial
from app.product_api import (
    InventoryCategoryInput,
    InventoryCategoryUpdateInput,
    InventoryDispatchInput,
    StockReceiptInput,
    inventory_report,
    list_inventory,
    list_inventory_movements,
    create_inventory_category,
    dispatch_inventory,
    receive_inventory,
    update_inventory_category,
)
from app.roles import ROLE_PERMISSIONS


def test_category_updates_keep_catalog_links_and_soft_deactivate() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        category = create_inventory_category(InventoryCategoryInput(name="Consumibles", description="Uso general"), admin, db)
        item = InventoryItem(name="Sellador", category=category["name"], category_id=category["id"], unit="pieza")
        db.add(item)
        db.commit()
        updated = update_inventory_category(category["id"], InventoryCategoryUpdateInput(name="Material de consumo", active=False), admin, db)
        db.refresh(item)
        assert updated["active"] is False
        assert updated["product_count"] == 1
        assert item.category_id == category["id"]
        assert item.category == "Material de consumo"
        assert db.query(InventoryCategory).count() == 1


def test_dispatch_links_a_folio_and_preserves_other_installation_reservations() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente")
        db.add(customer)
        db.flush()
        selected = Installation(customer_id=customer.id, folio="AE-SELECTED", status="assigned")
        other = Installation(customer_id=customer.id, folio="AE-OTHER", status="assigned")
        item = InventoryItem(name="Panel", unit="pieza", quantity=10, unit_cost=100)
        db.add_all([selected, other, item])
        db.flush()
        db.add_all([
            WorkOrderMaterial(installation_id=selected.id, item_id=item.id, requested_quantity=4, preissued_quantity=0, consumed_quantity=0, unit_cost=100),
            WorkOrderMaterial(installation_id=other.id, item_id=item.id, requested_quantity=5, preissued_quantity=0, consumed_quantity=0, unit_cost=100),
        ])
        db.commit()

        result = dispatch_inventory(InventoryDispatchInput(item_id=item.id, quantity=4, installation_id=selected.id, department="Técnicos", reason="Material para instalación"), admin, db)
        movement = db.query(InventoryMovement).one()
        assert movement.folio.startswith("SAL-")
        assert movement.installation_id == selected.id
        assert movement.source_type == "work_order"
        assert movement.department == "Técnicos"
        assert result["item"]["quantity"] == Decimal("6.00")

        with pytest.raises(HTTPException) as unavailable:
            dispatch_inventory(InventoryDispatchInput(item_id=item.id, quantity=2, reason="Salida general"), admin, db)
        assert unavailable.value.status_code == 409


def test_inventory_report_uses_business_day_and_marks_zero_stock_as_alert(monkeypatch) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        item = InventoryItem(name="Panel agotado", unit="pieza", quantity=0, minimum_quantity=0)
        db.add(item)
        db.flush()
        db.add(InventoryMovement(item_id=item.id, quantity=1, movement_type="in", reason="Entrada", created_by="admin", created_at=datetime(2026, 11, 17, 2, tzinfo=timezone.utc)))
        db.commit()
        monkeypatch.setattr("app.product_api.business_today", lambda: date(2026, 11, 16))
        result = inventory_report(month="2026-11", identity=manager, db=db)
        assert result["totals"]["entries_today"] == 1
        assert result["totals"]["exits_today"] == 0
        assert result["low_stock_items"][0]["id"] == item.id


def test_inventory_reader_cannot_request_inactive_catalog_records() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    reader = AuthIdentity("installer", "arcoenergy", frozenset({"instalador"}), frozenset({"inventory:read"}), "field@example.test", "Installer")
    with Session(engine) as db, pytest.raises(HTTPException) as denied:
        list_inventory(active=False, identity=reader, db=db)
    assert denied.value.status_code == 403


def test_manual_receipt_keeps_supplier_invoice_and_folio_in_kardex() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        item = InventoryItem(name="Inversor", quantity=0, unit="pieza")
        supplier = Supplier(name="Proveedor Solar")
        db.add_all([item, supplier])
        db.commit()
        receive_inventory(StockReceiptInput(item_id=item.id, quantity=2, unit_cost=12500, supplier_id=supplier.id, invoice_number="FAC-109", reason="Recepción manual"), admin, db)
        movement = list_inventory_movements(identity=admin, db=db)[0]
        assert movement["folio"].startswith("ENT-")
        assert movement["supplier_name"] == "Proveedor Solar"
        assert movement["invoice_reference"] == "FAC-109"
