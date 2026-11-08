import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_source_link_migration_appends_versions_without_changing_literal():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080066_history_card_source_links.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {
        "US-39": "CRM original completo",
        "US-40": "PWA original completo",
        "US-41": "Web original completo",
        "US-42": "History cards original completo",
    }
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1,
                "iteration": "source", "stakeholder": "Dueño del producto",
                "source_literal": literal, "source_type": "Conversación del proyecto",
                "source_reference": "docs/discovery/sources/owner-product-brief-2026-11-06.md",
                "normalized_story": "Interpretación inicial", "acceptance_criteria": [],
                "unresolved_questions": [], "linked_cards": [], "source_artifact": {"artifacts": []},
                "source_language": "es", "source_attribution": "Dueño del producto",
                "source_confidence": "needs_validation", "source_links": [],
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.story_id.in_(list(literals)))
            .order_by(HistoryCard.story_id, HistoryCard.version)
        ).mappings().all()

    for story_id, literal in literals.items():
        versions = [row for row in rows if row["story_id"] == story_id]
        assert [row["version"] for row in versions] == [1, 2]
        assert [row["source_literal"] for row in versions] == [literal, literal]
        assert versions[1]["source_links"][0]["location"]
        assert versions[1]["source_confidence"] == "verbatim_excerpt"
    assert rows[1]["source_links"][0]["excerpt"] == migration.REVISIONS["US-39"]["excerpt"]
    assert rows[3]["normalized_story"] == migration.REVISIONS["US-40"]["normalized_story"]
    assert rows[5]["normalized_story"] == migration.REVISIONS["US-41"]["normalized_story"]
    assert "El API permite consultar tarjetas y añadir una nueva versión append-only." in rows[7]["acceptance_criteria"]
