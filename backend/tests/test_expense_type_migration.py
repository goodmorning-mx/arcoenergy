import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, select, text

from app.models import HistoryCard


def test_expense_type_migration_preserves_legacy_expenses_and_history_sources():
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611090078_expense_type_fixed_variable.py"
    spec = importlib.util.spec_from_file_location("expense_type_migration", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    history = HistoryCard.__table__
    sources = {story_id: f"literal de fuente {story_id}" for story_id in migration.REVISIONS}
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_expenses (id VARCHAR(36) PRIMARY KEY, amount NUMERIC NOT NULL)"))
        connection.execute(text("INSERT INTO ae_expenses (id, amount) VALUES ('legacy', 10)"))
        history.create(connection)
        connection.execute(history.insert(), [
            {
                "id": f"source-{story_id}", "story_id": story_id, "version": 1,
                "iteration": "original", "stakeholder": "Mario Groso",
                "source_literal": source, "source_type": "WhatsApp", "source_reference": "source.md",
                "normalized_story": "Gastos fijos y variables", "acceptance_criteria": [],
                "unresolved_questions": [], "linked_cards": [], "recorded_by": "stakeholder",
                "created_at": datetime.now(timezone.utc),
            }
            for story_id, source in sources.items()
        ])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_expenses")}
        assert "expense_type" in columns
        assert connection.execute(text("SELECT expense_type FROM ae_expenses WHERE id='legacy'")).scalar_one() == "unclassified"
        versions = connection.execute(select(history).order_by(history.c.story_id, history.c.version)).mappings().all()
        for story_id, source in sources.items():
            rows = [row for row in versions if row["story_id"] == story_id]
            assert [row["version"] for row in rows] == [1, 2]
            assert rows[0]["source_literal"] == rows[1]["source_literal"] == source
