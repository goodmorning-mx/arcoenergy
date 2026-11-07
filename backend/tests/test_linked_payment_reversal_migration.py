import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


def test_linked_payment_reversal_migration_adds_append_only_links_and_downgrades() -> None:
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location(
        "linked_payment_reversals",
        root / "alembic" / "versions" / "202611060026_linked_payment_reversals.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")

    with engine.begin() as connection:
        for table in ("ae_supplier_payments", "ae_customer_payments"):
            connection.execute(text(f"CREATE TABLE {table} (id VARCHAR(36) PRIMARY KEY)"))
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()

        for table in ("ae_supplier_payments", "ae_customer_payments"):
            inspector = inspect(connection)
            assert "reversal_of_id" in {column["name"] for column in inspector.get_columns(table)}
            assert any(item["name"].endswith("payment_reversal") for item in inspector.get_unique_constraints(table))
            assert any(item["name"].endswith("payment_reversal") for item in inspector.get_foreign_keys(table))

        migration.downgrade()
        for table in ("ae_supplier_payments", "ae_customer_payments"):
            assert "reversal_of_id" not in {column["name"] for column in inspect(connection).get_columns(table)}
