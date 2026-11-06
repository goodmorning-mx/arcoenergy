from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InventoryItem, InventoryMovement
from app.product_api import InventoryReturnInput, list_inventory_movements, return_inventory


def setup_inventory():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = Session(engine)
    customer = Customer(name="Proyecto solar")
    db.add(customer)
    db.flush()
    installation = Installation(customer_id=customer.id, lead_installer="campo@example.test")
    item = InventoryItem(name="Riel", unit="pieza", quantity=0, unit_cost=100)
    db.add_all([installation, item])
    db.flush()
    issue = InventoryMovement(
        item_id=item.id, installation_id=installation.id, quantity=5,
        movement_type="out", unit_cost=100, reason="Salida a obra",
        created_by="coordinador", created_at=datetime(2026, 11, 6, tzinfo=timezone.utc),
    )
    db.add(issue)
    db.commit()
    return db, item, installation, issue


def test_return_replenishes_inventory_and_tracks_source_exit() -> None:
    db, item, _installation, issue = setup_inventory()
    identity = AuthIdentity("field-1", "arcoenergy", frozenset({"instalador"}), frozenset({"inventory:write", "inventory:read"}), "campo@example.test", "Campo")

    result = return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=4), identity, db)
    movements = list_inventory_movements(identity=identity, db=db)

    assert float(result["item"]["quantity"]) == 4
    assert result["movement"]["related_movement_id"] == issue.id
    assert [(movement["movement_type"], movement["returnable_quantity"]) for movement in movements if movement["movement_type"] == "out"] == [("out", 1)]
    assert [movement["signed_quantity"] for movement in movements] == [4, -5]
    assert "unit_cost" not in result["movement"]
    db.close()


def test_return_cannot_exceed_unreturned_issue_quantity() -> None:
    db, _item, _installation, issue = setup_inventory()
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:write"}), "admin@example.test", "Admin")
    return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=4), identity, db)

    with pytest.raises(HTTPException) as error:
        return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=2), identity, db)

    assert error.value.status_code == 409
    db.close()


def test_installer_cannot_return_material_from_another_persons_work_order() -> None:
    db, _item, _installation, issue = setup_inventory()
    identity = AuthIdentity("field-2", "arcoenergy", frozenset({"instalador"}), frozenset({"inventory:write"}), "otra@example.test", "Otro")

    with pytest.raises(HTTPException) as error:
        return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=1), identity, db)

    assert error.value.status_code == 403
    db.close()
