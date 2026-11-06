from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

from app.models import Base


def test_inventory_catalog_migration_accepts_columns_created_by_initial_metadata() -> None:
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202611060024_inventory_catalog_identifiers.py"
    spec = spec_from_file_location("inventory_catalog_identifiers", migration_path)
    migration = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("ae_inventory")}
    indexes = {index["name"] for index in inspector.get_indexes("ae_inventory")}
    assert {"description", "category", "brand", "model", "supplier_id", "barcode"} <= columns
    assert {"ix_ae_inventory_supplier_id", "uq_ae_inventory_barcode"} <= indexes
