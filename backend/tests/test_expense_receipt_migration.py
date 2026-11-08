import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect, text

from app.models import Base


def load_migration():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080069_expense_receipts_drive.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_expense_receipt_migration_adds_metadata_idempotently_and_preserves_existing_links():
    migration = load_migration()

    engine = create_engine("sqlite://")
    metadata = MetaData()
    Table("ae_expenses", metadata, Column("id", String(36), primary_key=True), Column("receipt_url", String), Column("amount", Integer))
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO ae_expenses (id, receipt_url, amount) VALUES ('expense-1', 'https://example.test/r', 100)"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"]: column for column in inspect(connection).get_columns("ae_expenses")}
        assert {"receipt_drive_file_id", "receipt_filename", "receipt_content_type", "receipt_updated_at"} <= set(columns)
        row = connection.execute(text("SELECT id, receipt_url, receipt_drive_file_id, receipt_filename FROM ae_expenses")).mappings().one()
        assert row["receipt_url"] == "https://example.test/r"
        assert row["receipt_drive_file_id"] == ""
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns_after_repeat = {column["name"] for column in inspect(connection).get_columns("ae_expenses")}

    assert {"receipt_drive_file_id", "receipt_filename", "receipt_content_type", "receipt_updated_at"} <= columns_after_repeat


def test_expense_receipt_migration_skips_columns_created_by_current_orm():
    migration = load_migration()
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        before = {column["name"] for column in inspect(connection).get_columns("ae_expenses")}
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        after = {column["name"] for column in inspect(connection).get_columns("ae_expenses")}

    names = {"receipt_drive_file_id", "receipt_filename", "receipt_content_type", "receipt_updated_at"}
    assert names <= before
    assert before == after
