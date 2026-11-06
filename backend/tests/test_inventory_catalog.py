from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, InventoryItem, Supplier
from app.product_api import InventoryItemInput, create_inventory_item
from app.roles import ROLE_PERMISSIONS


def test_inventory_catalog_keeps_metadata_and_unique_scannable_code() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor Solar")
        db.add(supplier); db.commit()
        item = create_inventory_item(InventoryItemInput(
            name="Panel 610 W", description="Panel bifacial", category="Módulos", brand="Marca solar",
            model="MS-610", supplier_id=supplier.id, barcode="7501234567890", unit="pieza",
            minimum_quantity=2, initial_quantity=4, unit_cost=Decimal("3500"),
        ), manager, db)
        stored = db.get(InventoryItem, item["id"])
        assert stored is not None
        assert (stored.category, stored.brand, stored.model, stored.supplier_id, stored.barcode) == (
            "Módulos", "Marca solar", "MS-610", supplier.id, "7501234567890",
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
