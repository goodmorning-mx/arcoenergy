import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, Customer, Installation, InventoryItem, InventoryMovement, WorkOrderMaterial


ROOT = Path(__file__).resolve().parents[1]


def test_migration_backfills_net_consumption_with_original_date_and_is_idempotent() -> None:
    spec = importlib.util.spec_from_file_location(
        "material_consumption_events_migration",
        ROOT / "alembic" / "versions" / "202611060017_material_consumption_events.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with Session(engine) as db:
        Base.metadata.create_all(engine)
        customer = Customer(name="Cliente")
        db.add(customer); db.flush()
        installation = Installation(customer_id=customer.id, folio="AE-OT-MIG")
        item = InventoryItem(name="Riel", quantity=5, unit_cost=120)
        db.add_all([installation, item]); db.flush()
        material = WorkOrderMaterial(installation_id=installation.id, item_id=item.id, requested_quantity=5,
            preissued_quantity=5, consumed_quantity=3, unit_cost=120)
        db.add(material); db.flush()
        source = InventoryMovement(item_id=item.id, installation_id=installation.id, work_order_material_id=material.id,
            quantity=5, movement_type="out", unit_cost=120, reason="consumo en instalación",
            created_by="instalador", created_at=datetime(2026, 10, 28, tzinfo=timezone.utc))
        returned = InventoryMovement(item_id=item.id, installation_id=installation.id, work_order_material_id=material.id,
            quantity=2, movement_type="return", related_movement_id="", unit_cost=120, reason="sobrante", created_by="instalador")
        db.add(source); db.flush(); returned.related_movement_id = source.id; db.add(returned); db.commit()
        source_id = source.id
        with engine.begin() as connection:
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
                migration.upgrade()
        events = db.scalars(select(InventoryMovement).where(InventoryMovement.movement_type == "consumption")).all()

    assert len(events) == 1
    assert float(events[0].quantity) == 3
    assert events[0].related_movement_id == source_id
    assert events[0].created_at.replace(tzinfo=timezone.utc) == datetime(2026, 10, 28, tzinfo=timezone.utc)
