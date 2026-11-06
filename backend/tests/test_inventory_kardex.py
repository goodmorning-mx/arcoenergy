from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InventoryItem, InventoryMovement
from app.product_api import list_inventory_movements


def test_inventory_kardex_shows_signed_stock_changes_and_hides_cost_from_field_role() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        item = InventoryItem(name="Riel", unit="pieza", quantity=3, minimum_quantity=1, unit_cost=120)
        db.add(item)
        db.flush()
        customer = Customer(name="Proyecto Tampico")
        db.add(customer)
        db.flush()
        installation = Installation(customer_id=customer.id, lead_installer="campo@example.test")
        db.add(installation)
        db.flush()
        db.add_all([
            InventoryMovement(
                item_id=item.id, quantity=4, movement_type="in", unit_cost=120,
                reason="recepción proveedor", created_by="compras",
                created_at=datetime(2026, 11, 5, 10, tzinfo=timezone.utc),
            ),
            InventoryMovement(
                item_id=item.id, quantity=1, movement_type="out", unit_cost=120,
                installation_id=installation.id, reason="instalación", created_by="campo",
                created_at=datetime(2026, 11, 6, 10, tzinfo=timezone.utc),
            ),
        ])
        db.commit()

        rows = list_inventory_movements(
            identity=AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), frozenset({"inventory:read"}), "campo@example.test", "Campo"),
            db=db,
        )
        admin_rows = list_inventory_movements(
            identity=AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:read", "inventory:costs:read"}), "admin@example.test", "Admin"),
            db=db,
        )

    assert [row["signed_quantity"] for row in rows] == [-1]
    assert rows[0]["item_name"] == "Riel"
    assert "unit_cost" not in rows[0]
    assert [row["signed_quantity"] for row in admin_rows] == [-1, 4]
    assert all(row["unit_cost"] == 120 for row in admin_rows)


def test_inventory_kardex_rejects_inverted_date_range() -> None:
    with pytest.raises(HTTPException) as error:
        list_inventory_movements(
            from_date=date(2026, 11, 7),
            to_date=date(2026, 11, 6),
            identity=AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:read"}), "admin@example.test", "Admin"),
            db=object(),
        )

    assert error.value.status_code == 422
