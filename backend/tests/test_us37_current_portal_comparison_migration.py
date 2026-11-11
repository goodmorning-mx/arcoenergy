import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us37_portal_comparison_appends_and_preserves_source_literal() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611110125_us37_current_portal_comparison.py"
    spec = importlib.util.spec_from_file_location("us37_portal_comparison", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    source = "Comparar las pestañas del sistema de César para que quede igual o parecido."

    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), {
            "id": "us37-original", "story_id": "US-37", "version": 1,
            "iteration": "Iteración anterior", "stakeholder": "Mario Groso",
            "source_literal": source, "source_type": "Conversación y documento",
            "source_reference": "history-cards.md", "normalized_story": "Comparar los apartados de administración",
            "acceptance_criteria": ["Registrar función de cada sección."], "unresolved_questions": [],
            "linked_cards": [], "recorded_by": "stakeholder",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.version)).mappings().all()
        assert [row["version"] for row in rows] == [1, 2]
        assert all(row["source_literal"] == source for row in rows)
        assert len(rows[1]["acceptance_criteria"]) == 3
        assert len(rows[1]["unresolved_questions"]) == 1
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        remaining = connection.execute(select(table)).mappings().all()
        assert len(remaining) == 1 and remaining[0]["source_literal"] == source
