import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_live_route_audit_appends_to_related_cards_without_replacing_sources() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611100091_live_route_auth_audit_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    sources = {"US-14": "Cada usuario tendrá privilegios.", "US-39": "El CRM es el sistema de administración.",
               "US-40": "El PWA es una aplicación móvil operativa."}
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        for index, (story_id, source) in enumerate(sources.items(), 1):
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "initial",
                "stakeholder": "stakeholder", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": source, "normalized_story": f"Story {story_id}",
                "acceptance_criteria": [f"original-{index}"], "unresolved_questions": ["original-question"],
                "linked_cards": [], "recorded_by": "source-import", "created_at": now,
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).order_by(
            HistoryCard.story_id, HistoryCard.version,
        )).mappings().all()

    assert len(cards) == 6
    for story_id, source in sources.items():
        versions = [card for card in cards if card["story_id"] == story_id]
        assert [card["version"] for card in versions] == [1, 2]
        assert all(card["source_literal"] == source for card in versions)
        assert versions[1]["acceptance_criteria"][0].startswith("original-")
        assert versions[1]["unresolved_questions"][0] == "original-question"
        assert any("rechazan solicitudes anónimas" in item for item in versions[1]["acceptance_criteria"])
