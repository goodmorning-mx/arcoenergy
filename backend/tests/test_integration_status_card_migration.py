import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_integration_status_migration_appends_us13_without_rewriting_source_literal():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070049_integration_status_truth_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literal = "[11:22 p.m., 26/10/2026] Goito Profugo: Que todo se vaya a un drive para almacenar todos los datos"
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-13", "version": 1, "iteration": "source",
            "stakeholder": "Goito Profugo", "source_type": "WhatsApp", "source_reference": "source",
            "source_literal": literal, "normalized_story": "Guardar documentación en Drive",
            "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
            "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
            "source_attribution": "Goito Profugo", "source_confidence": "needs_validation",
            "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-13")
                                   .order_by(HistoryCard.version)).mappings().all()
    assert len(cards) == 2
    assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
    assert cards[1]["recorded_by"] == "system:implementation-iteration"
