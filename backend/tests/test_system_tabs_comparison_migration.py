import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_system_comparison_revision_keeps_literal_us37_source_unchanged() -> None:
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location(
        "system_tabs_comparison_card_revision",
        root / "alembic" / "versions" / "202611060032_system_tabs_comparison_card_revision.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    literal = "Mario: revisar las pestañas y secciones del sistema actual."
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert().values(
            id="us37-source", story_id="US-37", version=1, iteration="iteración 1", stakeholder="Mario Groso",
            source_literal=literal, source_type="Conversación", source_reference="source.md",
            normalized_story="Comparar secciones", acceptance_criteria=[], unresolved_questions=[],
            linked_cards=[], recorded_by="stakeholder", created_at=datetime.now(timezone.utc),
        ))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.version)).mappings().all()
        assert [row["version"] for row in rows] == [1, 2]
        assert all(row["source_literal"] == literal for row in rows)
        assert rows[1]["linked_cards"] == ["US-15", "US-21", "US-25", "US-32", "US-33", "US-38"]
        assert "Plan 24" in rows[1]["acceptance_criteria"][-1]
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert len(connection.execute(select(table)).all()) == 1
