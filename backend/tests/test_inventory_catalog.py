from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, InventoryItem, InventoryMovement, Supplier
from app.product_api import InventoryItemInput, InventoryItemUpdateInput, PurchaseCatalogItemInput, _serialize_inventory_item, create_inventory_item, create_purchase_catalog_item, update_inventory_item
from app.roles import ROLE_PERMISSIONS


def test_inventory_catalog_keeps_metadata_and_unique_scannable_code() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor Solar")
        db.add(supplier); db.commit()
        item = create_inventory_item(InventoryItemInput(
            name="Panel 610 W", description="Panel bifacial", category="Módulos", subcategory="Bifacial", brand="Marca solar",
            model="MS-610", supplier_id=supplier.id, barcode="7501234567890", unit="pieza",
            minimum_quantity=2, initial_quantity=4, unit_cost=Decimal("3500"),
        ), manager, db)
        stored = db.get(InventoryItem, item["id"])
        assert stored is not None
        assert (stored.category, stored.subcategory, stored.brand, stored.model, stored.supplier_id, stored.barcode) == (
            "Módulos", "Bifacial", "Marca solar", "MS-610", supplier.id, "7501234567890",
        )
        with pytest.raises(HTTPException) as duplicate:
            create_inventory_item(InventoryItemInput(name="Otro artículo", barcode="7501234567890"), manager, db)
        assert duplicate.value.status_code == 409


def test_inventory_catalog_rejects_unknown_supplier() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db, pytest.raises(HTTPException) as missing:
        create_inventory_item(InventoryItemInput(name="Panel solar", supplier_id="missing-supplier"), manager, db)
    assert missing.value.status_code == 422


def test_inventory_catalog_edit_updates_metadata_without_changing_on_hand_stock() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        original = create_inventory_item(InventoryItemInput(
            name="Panel 610 W", barcode="A-610", initial_quantity=8, unit_cost=3500,
        ), manager, db)
        edited = update_inventory_item(original["id"], InventoryItemUpdateInput(
            name="Panel 620 W", category="Módulos", subcategory="Monocristalino", brand="Solar Co", model="SC-620",
            barcode="A-620", unit="pieza", minimum_quantity=2, unit_cost=3700,
        ), manager, db)
        stored = db.get(InventoryItem, original["id"])
        assert edited["name"] == "Panel 620 W"
        assert edited["subcategory"] == "Monocristalino"
        assert stored.quantity == Decimal("8.00")
        assert stored.unit_cost == Decimal("3700.00")


def test_accountant_can_add_zero_stock_catalog_item_from_purchase_flow() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    accountant = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        item = create_purchase_catalog_item(PurchaseCatalogItemInput(
            name="Protector DC", category="Protección", subcategory="Corriente directa", unit="pieza",
        ), accountant, db)
        stored = db.get(InventoryItem, item["id"])
        assert stored is not None
        assert (stored.quantity, stored.minimum_quantity, stored.unit_cost, stored.subcategory) == (0, 0, 0, "Corriente directa")
        assert db.query(InventoryMovement).count() == 0


def test_inventory_catalog_edit_rejects_duplicate_code_and_unknown_article() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        first = create_inventory_item(InventoryItemInput(name="Panel solar", barcode="ORIGINAL"), manager, db)
        create_inventory_item(InventoryItemInput(name="Inversor solar", barcode="DUP"), manager, db)
        with pytest.raises(HTTPException) as duplicate:
            update_inventory_item(first["id"], InventoryItemUpdateInput(name="Panel solar", barcode="DUP"), manager, db)
        assert duplicate.value.status_code == 409
        with pytest.raises(HTTPException) as missing:
            update_inventory_item("missing", InventoryItemUpdateInput(name="Panel solar"), manager, db)
        assert missing.value.status_code == 404


def test_inventory_api_hides_restock_owner_and_internal_alert_flag_from_field_role() -> None:
    item = InventoryItem(
        name="Microinversor", unit="pieza", quantity=2, minimum_quantity=3,
        restock_responsible_email="installer@example.test", low_stock_alert_active=True,
        unit_cost=Decimal("3500"),
    )
    installer = AuthIdentity("installer", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "installer@example.test", "Instalador")
    manager = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")

    field_view = _serialize_inventory_item(item, installer)
    manager_view = _serialize_inventory_item(item, manager)

    assert "restock_responsible_email" not in field_view
    assert "low_stock_alert_active" not in field_view
    assert "unit_cost" not in field_view
    assert manager_view["restock_responsible_email"] == "installer@example.test"
    assert "low_stock_alert_active" not in manager_view
