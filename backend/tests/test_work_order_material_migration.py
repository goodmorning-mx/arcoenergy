import importlib.util
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


ROOT = Path(__file__).resolve().parents[1]


def test_reservation_migration_repairs_legacy_duplicate_sale_and_field_issue() -> None:
    spec = importlib.util.spec_from_file_location(
        "work_order_material_migration",
        ROOT / "alembic" / "versions" / "202611060015_work_order_material_reservations.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    ids = [str(uuid4()) for _ in range(6)]
    installation_id, item_id, sale_id, sale_issue_id, field_issue_id, customer_id = ids

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_installations (id VARCHAR(36) PRIMARY KEY, folio VARCHAR(36))"))
        connection.execute(text("CREATE TABLE ae_inventory (id VARCHAR(36) PRIMARY KEY, quantity NUMERIC(12,2), unit_cost NUMERIC(12,2))"))
        connection.execute(text("CREATE TABLE ae_sales (id VARCHAR(36) PRIMARY KEY, folio VARCHAR(36), installation_id VARCHAR(36))"))
        connection.execute(text("""CREATE TABLE ae_inventory_movements (
            id VARCHAR(36) PRIMARY KEY, item_id VARCHAR(36), installation_id VARCHAR(36),
            quantity NUMERIC(12,2), movement_type VARCHAR(20), unit_cost NUMERIC(12,2),
            related_movement_id VARCHAR(36), purchase_line_id VARCHAR(36), reason VARCHAR(180),
            created_by VARCHAR(180), created_at DATETIME)"""))
        connection.execute(text("INSERT INTO ae_installations (id, folio) VALUES (:id, 'AE-OT-1')"), {"id": installation_id})
        connection.execute(text("INSERT INTO ae_inventory (id, quantity, unit_cost) VALUES (:id, 12, 100)"), {"id": item_id})
        connection.execute(text("INSERT INTO ae_sales (id, folio, installation_id) VALUES (:id, 'AE-V-1', :installation)"), {"id": sale_id, "installation": installation_id})
        connection.execute(text("""INSERT INTO ae_inventory_movements
            (id, item_id, installation_id, quantity, movement_type, unit_cost, reason, created_by)
            VALUES (:id, :item, :installation, 8, 'out', 100, 'Orden AE-OT-1 · Venta AE-V-1', 'admin')"""),
            {"id": sale_issue_id, "item": item_id, "installation": installation_id})
        connection.execute(text("""INSERT INTO ae_inventory_movements
            (id, item_id, installation_id, quantity, movement_type, unit_cost, reason, created_by)
            VALUES (:id, :item, :installation, 4, 'out', 100, 'consumo instalación', 'campo')"""),
            {"id": field_issue_id, "item": item_id, "installation": installation_id})
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        material = connection.execute(text("SELECT requested_quantity, preissued_quantity, consumed_quantity FROM ae_work_order_materials")).one()
        stock = connection.execute(text("SELECT quantity FROM ae_inventory WHERE id=:id"), {"id": item_id}).scalar_one()
        corrections = connection.execute(text("SELECT COUNT(*) FROM ae_inventory_movements WHERE movement_type='return' AND related_movement_id=:id"), {"id": field_issue_id}).scalar_one()
        assert "work_order_material_id" in {column["name"] for column in inspect(connection).get_columns("ae_inventory_movements")}

    assert tuple(map(float, material)) == (8.0, 8.0, 4.0)
    assert float(stock) == 16.0
    assert corrections == 1
