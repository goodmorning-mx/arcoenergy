import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us41_public_agent_revision_preserves_original_source() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611110126_us41_public_agent_contact_consent.py"
    spec = importlib.util.spec_from_file_location("us41_public_contact", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    source = "La página web va a cotizar por IA agentica hablando con el cliente."

    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), {
            "id": "us41-original", "story_id": "US-41", "version": 1,
            "iteration": "Iteración inicial", "stakeholder": "Dueño de Arco Energy",
            "source_literal": source, "source_type": "Conversación",
            "source_reference": "owner-product-brief-2026-11-06.md", "normalized_story": "Cotizar por agente público",
            "acceptance_criteria": ["Usar el catálogo autorizado."], "unresolved_questions": [],
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
