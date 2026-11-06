from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text


def test_inventory_migration_backfills_direction_without_fabricating_historical_costs() -> None:
    migration_file = Path(__file__).parents[1] / "alembic" / "versions" / "202611060004_inventory_kardex.py"
    spec = spec_from_file_location("inventory_kardex_migration", migration_file)
    migration = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_inventory (id VARCHAR(36) PRIMARY KEY, unit_cost NUMERIC(12,2) NOT NULL)"))
        connection.execute(text("""
            CREATE TABLE ae_inventory_movements (
                id VARCHAR(36) PRIMARY KEY, item_id VARCHAR(36) NOT NULL,
                installation_id VARCHAR(36), quantity NUMERIC(12,2) NOT NULL,
                reason VARCHAR(180), created_by VARCHAR(180), created_at DATETIME
            )
        """))
        connection.execute(text("INSERT INTO ae_inventory VALUES ('item-1', 45.5)"))
        connection.execute(text("INSERT INTO ae_inventory_movements VALUES ('in-1','item-1',NULL,5,'existencia inicial','admin',CURRENT_TIMESTAMP)"))
        connection.execute(text("INSERT INTO ae_inventory_movements VALUES ('out-1','item-1','install-1',2,'consumo','campo',CURRENT_TIMESTAMP)"))
        migration.op = Operations(MigrationContext.configure(connection))

        migration.upgrade()

        rows = connection.execute(text("SELECT id, movement_type, unit_cost FROM ae_inventory_movements ORDER BY id")).all()

    assert [(row.id, row.movement_type, row.unit_cost) for row in rows] == [
        ("in-1", "in", None),
        ("out-1", "out", None),
    ]
