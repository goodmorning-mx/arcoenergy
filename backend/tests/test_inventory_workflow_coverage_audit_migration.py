import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_inventory_workflow_audit_appends_versions_without_changing_sources() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611110124_inventory_workflow_coverage_audit.py"
    spec = importlib.util.spec_from_file_location("inventory_workflow_audit", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    sources = {story_id: f"Fuente literal conservada para {story_id}." for story_id in migration.CRITERIA}

    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), [{
            "id": f"{story_id}-original", "story_id": story_id, "version": 1,
            "iteration": "Iteración anterior", "stakeholder": "Stakeholder",
            "source_literal": source, "source_type": "Conversación",
            "source_reference": "history-cards.md", "normalized_story": f"Historia {story_id}",
            "acceptance_criteria": ["Criterio original."], "unresolved_questions": [],
            "linked_cards": [], "recorded_by": "stakeholder",
            "created_at": datetime.now(timezone.utc),
        } for story_id, source in sources.items()])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
        assert len(rows) == 8
        for index, story_id in enumerate(sorted(sources)):
            original, revised = rows[index * 2:index * 2 + 2]
            assert (original["story_id"], original["version"]) == (story_id, 1)
            assert (revised["story_id"], revised["version"]) == (story_id, 2)
            assert original["source_literal"] == revised["source_literal"] == sources[story_id]
            assert len(revised["acceptance_criteria"]) == 2
            assert len(revised["unresolved_questions"]) == 1
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        remaining = connection.execute(select(table)).mappings().all()
        assert len(remaining) == 4
        assert {row["source_literal"] for row in remaining} == set(sources.values())
