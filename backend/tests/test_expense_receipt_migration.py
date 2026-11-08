import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect, text


def test_expense_receipt_migration_adds_private_file_metadata_and_removes_it_on_downgrade():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080069_expense_receipts_drive.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

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
            migration.downgrade()
        columns_after_downgrade = {column["name"] for column in inspect(connection).get_columns("ae_expenses")}

    assert not {"receipt_drive_file_id", "receipt_filename", "receipt_content_type", "receipt_updated_at"} & columns_after_downgrade
