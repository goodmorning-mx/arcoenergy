from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InventoryItem, InventoryMovement, WorkOrderMaterial
from app.product_api import StockIssueInput, issue_work_order_materials, list_installations
from app.roles import ROLE_PERMISSIONS


def setup_orders():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = Session(engine)
    customer = Customer(name="Proyecto")
    db.add(customer); db.flush()
    order = Installation(customer_id=customer.id, folio="AE-TEST-1", status="assigned")
    other = Installation(customer_id=customer.id, folio="AE-TEST-2", status="assigned")
    item = InventoryItem(name="Panel", unit="pieza", quantity=12, unit_cost=100)
    db.add_all([order, other, item]); db.flush()
    material = WorkOrderMaterial(installation_id=order.id, item_id=item.id, requested_quantity=8,
        preissued_quantity=0, consumed_quantity=0, unit_cost=100)
    reservation = WorkOrderMaterial(installation_id=other.id, item_id=item.id, requested_quantity=5,
        preissued_quantity=0, consumed_quantity=0, unit_cost=100)
    db.add_all([material, reservation]); db.commit()
    identity = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}),
        ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    return db, order, other, item, material, identity


def test_issue_reduces_physical_stock_and_links_movement_to_requested_material():
    db, order, _other, item, material, identity = setup_orders()
    result = issue_work_order_materials(StockIssueInput(installation_id=order.id,
        document_reference="solicitud-001.pdf", lines=[{"work_order_material_id": material.id, "quantity": 4}]), identity, db)

    movement = db.query(InventoryMovement).one()
    assert result["folio"] == "AE-TEST-1"
    assert item.quantity == Decimal("8.00")
    assert material.preissued_quantity == Decimal("4.00")
    assert material.consumed_quantity == Decimal("0.00")
    assert movement.movement_type == "out"
    assert movement.work_order_material_id == material.id
    assert movement.installation_id == order.id
    assert movement.reason == "Salida de solicitud solicitud-001.pdf"
    db.close()


def test_issue_preserves_stock_reserved_for_other_work_orders():
    db, order, _other, item, material, identity = setup_orders()
    with pytest.raises(HTTPException) as error:
        issue_work_order_materials(StockIssueInput(installation_id=order.id,
            lines=[{"work_order_material_id": material.id, "quantity": 8}]), identity, db)
    assert error.value.status_code == 409
    assert item.quantity == Decimal("12.00")
    assert material.preissued_quantity == Decimal("0.00")
    assert db.query(InventoryMovement).count() == 0
    db.close()


def test_issue_rejects_material_from_another_order_and_closed_order():
    db, order, other, item, _material, identity = setup_orders()
    other_material = db.query(WorkOrderMaterial).filter_by(installation_id=other.id).one()
    with pytest.raises(HTTPException) as foreign:
        issue_work_order_materials(StockIssueInput(installation_id=order.id,
            lines=[{"work_order_material_id": other_material.id, "quantity": 1}]), identity, db)
    assert foreign.value.status_code == 422

    order.status = "closed"; db.commit()
    with pytest.raises(HTTPException) as closed:
        issue_work_order_materials(StockIssueInput(installation_id=order.id,
            lines=[{"work_order_material_id": _material.id, "quantity": 1}]), identity, db)
    assert closed.value.status_code == 409
    assert item.quantity == Decimal("12.00")
    db.close()


def test_issue_batch_does_not_commit_partial_stock_when_later_line_fails():
    db, order, _other, item, material, identity = setup_orders()
    second = InventoryItem(name="Inversor", unit="pieza", quantity=3, unit_cost=500)
    db.add(second); db.flush()
    second_material = WorkOrderMaterial(installation_id=order.id, item_id=second.id, requested_quantity=2,
        preissued_quantity=0, consumed_quantity=0, unit_cost=500)
    db.add(second_material); db.commit()
    payload = StockIssueInput(installation_id=order.id, lines=[
        {"work_order_material_id": material.id, "quantity": 1},
        {"work_order_material_id": second_material.id, "quantity": 3},
    ])
    with pytest.raises(HTTPException):
        issue_work_order_materials(payload, identity, db)
    db.rollback()
    assert db.get(InventoryItem, item.id).quantity == Decimal("12.00")
    assert db.get(WorkOrderMaterial, material.id).preissued_quantity == Decimal("0.00")
    assert db.query(InventoryMovement).count() == 0
    db.close()


def test_issue_rejects_duplicate_material_lines():
    _db, order, _other, _item, material, _identity = setup_orders()
    with pytest.raises(ValueError):
        StockIssueInput(installation_id=order.id, lines=[
            {"work_order_material_id": material.id, "quantity": 1},
            {"work_order_material_id": material.id, "quantity": 1},
        ])


def test_installation_materials_hide_cost_from_installer_but_keep_it_for_accountant():
    db, order, _other, _item, _material, _identity = setup_orders()
    order.lead_installer = "field@example.test"
    installer = AuthIdentity("field-1", "arcoenergy", frozenset({"instalador"}),
        frozenset({"installations:read", "inventory:read"}), "field@example.test", "Campo")
    accountant = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}),
        frozenset({"installations:read", "inventory:read", "inventory:costs:read"}), "accountant@example.test", "Contador")
    db.commit()

    field_material = next(row for row in list_installations(identity=installer, db=db) if row["id"] == order.id)["materials"][0]
    accountant_material = next(row for row in list_installations(identity=accountant, db=db) if row["id"] == order.id)["materials"][0]

    assert "unit_cost" not in field_material
    assert field_material["requested_quantity"] == 8
    assert accountant_material["unit_cost"] == Decimal("100.00")
    db.close()
