from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, InventoryItem, InventoryMovement
from app.product_api import InventoryMovementCorrectionInput, list_inventory_movements, reverse_manual_inventory_receipt


def test_manual_receipt_correction_is_append_only_and_updates_stock() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:manage", "inventory:read"}), "admin@example.test", "Admin")
    with Session(engine) as db:
        item = InventoryItem(name="Panel", unit="pieza", quantity=5, unit_cost=1250)
        db.add(item); db.flush()
        source = InventoryMovement(item_id=item.id, quantity=5, movement_type="in", unit_cost=1250, reason="captura duplicada", created_by="admin", created_at=datetime(2026, 11, 10, tzinfo=timezone.utc))
        db.add(source); db.commit()

        result = reverse_manual_inventory_receipt(source.id, InventoryMovementCorrectionInput(reason="Entrada duplicada"), identity, db)
        rows = list_inventory_movements(identity=identity, db=db)

        assert float(result["item"]["quantity"]) == 0
        assert result["movement"]["related_movement_id"] == source.id
        assert db.get(InventoryMovement, source.id) is not None
        assert {row["movement_type"]: row["signed_quantity"] for row in rows} == {"in": 5, "receipt_reversal": -5}
        original = next(row for row in rows if row["id"] == source.id)
        assert original["can_reverse"] is False
        assert original["correction_note"] == "Esta entrada ya tiene una corrección enlazada en el kardex."


@pytest.mark.parametrize("source_type,reason", [("purchase", "compra"), ("in", "existencia inicial")])
def test_only_manual_receipts_can_be_corrected(source_type: str, reason: str) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:manage"}), "admin@example.test", "Admin")
    with Session(engine) as db:
        item = InventoryItem(name="Panel", quantity=2, unit_cost=100)
        db.add(item); db.flush()
        source = InventoryMovement(item_id=item.id, quantity=2, movement_type=source_type, unit_cost=100, reason=reason, created_by="admin")
        db.add(source); db.commit()
        with pytest.raises(HTTPException) as error:
            reverse_manual_inventory_receipt(source.id, InventoryMovementCorrectionInput(reason="Corrección válida"), identity, db)
        assert error.value.status_code == 409


def test_receipt_with_later_activity_or_insufficient_stock_requires_reconciliation() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), frozenset({"inventory:manage"}), "admin@example.test", "Admin")
    with Session(engine) as db:
        item = InventoryItem(name="Panel", quantity=4, unit_cost=100)
        db.add(item); db.flush()
        source = InventoryMovement(item_id=item.id, quantity=5, movement_type="in", reason="recepción", created_at=datetime(2026, 11, 10, tzinfo=timezone.utc))
        db.add(source); db.flush()
        db.add(InventoryMovement(item_id=item.id, quantity=1, movement_type="out", reason="salida", created_at=datetime(2026, 11, 11, tzinfo=timezone.utc)))
        db.commit()
        with pytest.raises(HTTPException) as error:
            reverse_manual_inventory_receipt(source.id, InventoryMovementCorrectionInput(reason="Corrección válida"), identity, db)
        assert error.value.status_code == 409
        original = next(row for row in list_inventory_movements(identity=identity, db=db) if row["id"] == source.id)
        assert original["can_reverse"] is False
        assert "movimientos posteriores" in original["correction_note"]
        assert "conciliación" in original["correction_note"]
