import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_installer_contact_revision_preserves_source_cards_append_only():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080072_installer_contact_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literals = {"US-7": "Notificar a los instaladores que ya hay una instalación.", "US-14": "Cada usuario tendrá privilegios de ver información."}
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1,
                "iteration": "source", "stakeholder": "Stakeholder",
                "source_literal": literal, "source_type": "Mensaje de WhatsApp",
                "source_reference": "source", "normalized_story": "Campo",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_language": "es",
                "source_attribution": "Stakeholder", "source_confidence": "needs_validation",
                "source_links": [], "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id.in_(list(literals))).order_by(HistoryCard.story_id, HistoryCard.version)).mappings().all()

    assert len(rows) == 4
    for story_id, literal in literals.items():
        versions = [row for row in rows if row["story_id"] == story_id]
        assert [row["version"] for row in versions] == [1, 2]
        assert versions[0]["source_literal"] == versions[1]["source_literal"] == literal
        assert versions[1]["iteration"] == migration.ITERATION
    revised = {row["story_id"]: row for row in rows if row["version"] == 2}
    assert any("domicilio, teléfono y correo" in item for item in revised["US-7"]["acceptance_criteria"])
    assert any("datos necesarios" in item for item in revised["US-14"]["acceptance_criteria"])
