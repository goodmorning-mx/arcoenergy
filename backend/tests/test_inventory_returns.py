from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InventoryItem, InventoryMovement, WorkOrderMaterial
from app.product_api import InventoryReturnInput, _serialize_inventory_movement, list_inventory_movements, profitability_report, return_inventory


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


def test_inventory_movement_unit_cost_is_visible_only_with_cost_permission() -> None:
    db, _item, _installation, issue = setup_inventory()
    installer = AuthIdentity("field-1", "arcoenergy", frozenset({"instalador"}), frozenset({"inventory:read"}), "campo@example.test", "Campo")
    accountant = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), frozenset({"inventory:read", "inventory:costs:read"}), "accountant@example.test", "Cuenta")

    assert "unit_cost" not in _serialize_inventory_movement(issue, installer)
    assert _serialize_inventory_movement(issue, accountant)["unit_cost"] == Decimal("100.00")
    assert _serialize_inventory_movement(None, installer) is None
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


def test_damaged_preissued_material_is_recorded_as_waste_and_project_cost_without_restocking() -> None:
    db, item, installation, issue = setup_inventory()
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:write", "inventory:read"}), "admin@example.test", "Admin")
    material = WorkOrderMaterial(installation_id=installation.id, item_id=item.id, requested_quantity=5,
        preissued_quantity=5, consumed_quantity=0, unit_cost=100)
    db.add(material); db.commit()

    result = return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=2, condition="damaged"), identity, db)
    report = profitability_report(installation_id=installation.id, db=db)
    movements = list_inventory_movements(identity=identity, db=db)

    assert result["movement"]["movement_type"] == "damage"
    assert float(result["item"]["quantity"]) == 0
    assert db.get(InventoryItem, item.id).quantity == 0
    assert material.preissued_quantity == 5 and material.consumed_quantity == 2
    assert report["totals"]["materials_cost"] == Decimal("200.00")
    assert {(row["movement_type"], row["signed_quantity"]) for row in movements if row["movement_type"] in {"damage", "consumption"}} == {("consumption", 0), ("damage", 0)}
    assert next(row for row in movements if row["movement_type"] == "out")["returnable_quantity"] == 3
    db.close()
