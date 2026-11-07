import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_field_cache_logout_migration_appends_us14_and_us40_without_rewriting_source_literals():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070048_field_cache_logout_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {"US-14": "Si todo fuera desde una app, cada usuario tendrá privilegios de ver información", "US-40": "La PWA es una aplicacion mobile para las personas de campo."}
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "Goito Profugo", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": literal, "normalized_story": "Acceso y trabajo en PWA",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "Goito Profugo", "source_confidence": "needs_validation",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id.in_(list(literals)))
                                   .order_by(HistoryCard.story_id, HistoryCard.version)).mappings().all()
    assert {(row["story_id"], row["version"]) for row in cards} == {("US-14", 1), ("US-14", 2), ("US-40", 1), ("US-40", 2)}
    for story_id, literal in literals.items():
        versions = [row for row in cards if row["story_id"] == story_id]
        assert versions[0]["source_literal"] == versions[1]["source_literal"] == literal
        assert versions[1]["recorded_by"] == "system:implementation-iteration"
