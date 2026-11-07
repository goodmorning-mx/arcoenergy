import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, select

from app.models import HistoryCard


def test_offline_operation_receipts_and_card_revisions_are_migrated_append_only() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611060030_offline_field_operation_receipts.py"
    spec = importlib.util.spec_from_file_location("offline_field_operations", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    sources = {story_id: f"fuente literal original {story_id}" for story_id in migration.UPDATES}

    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), [
            {"id": f"original-{story_id}", "story_id": story_id, "version": 1,
             "iteration": "iteración 1", "stakeholder": "Instalador",
             "source_literal": source, "source_type": "Conversación",
             "source_reference": "source.md", "normalized_story": "Historia original",
             "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
             "recorded_by": "stakeholder", "created_at": datetime.now(timezone.utc)}
            for story_id, source in sources.items()
        ])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_offline_operations")}
        constraints = inspect(connection).get_unique_constraints("ae_offline_operations")
        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
        assert {"owner_email", "operation_id", "operation_type", "payload_hash", "result_id"} <= columns
        assert any(item["name"] == "uq_ae_offline_operation_owner_key" for item in constraints)
        assert len(rows) == 6
        for story_id, source in sources.items():
            versions = [row for row in rows if row["story_id"] == story_id]
            assert [row["version"] for row in versions] == [1, 2]
            assert versions[0]["source_literal"] == versions[1]["source_literal"] == source
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert inspect(connection).has_table("ae_offline_operations")
        remaining = connection.execute(select(table)).mappings().all()
        assert len(remaining) == 3
