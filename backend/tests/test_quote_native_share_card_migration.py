import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_native_share_migration_appends_us3_without_rewriting_literal():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070051_quote_native_share_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literal = "En cual sea de las dos opciones que sea desde una app o desde la computadora y se guarde foliado en un drive, al momento de que se genere en pdf en automático nos da la opción de enviarla vía WhatsApp al cliente"
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-3", "version": 1, "iteration": "source",
            "stakeholder": "Goito Profugo", "source_type": "WhatsApp", "source_reference": "source",
            "source_literal": literal, "normalized_story": "Compartir propuesta PDF por WhatsApp",
            "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
            "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
            "source_attribution": "Goito Profugo", "source_confidence": "needs_validation",
            "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-3")
                                      .order_by(HistoryCard.version)).mappings().all()
    assert len(versions) == 2
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == literal
    assert versions[1]["recorded_by"] == "system:implementation-iteration"
