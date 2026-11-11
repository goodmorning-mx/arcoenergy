import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_project_profitability_revision_appends_to_us12_and_us38_without_changing_sources() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611100092_project_profitability_filter_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    sources = {"US-12": "Controlar materiales y costos directos.", "US-38": "Costeos por proyecto y por mes."}
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        for index, (story_id, source) in enumerate(sources.items(), 1):
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "initial",
                "stakeholder": "Mario Groso", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": source, "normalized_story": f"Story {story_id}",
                "acceptance_criteria": [f"original-{index}"], "unresolved_questions": ["original-question"],
                "linked_cards": [], "recorded_by": "source-import", "created_at": now,
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).order_by(
            HistoryCard.story_id, HistoryCard.version,
        )).mappings().all()

    assert len(cards) == 4
    for story_id, source in sources.items():
        versions = [card for card in cards if card["story_id"] == story_id]
        assert [card["version"] for card in versions] == [1, 2]
        assert all(card["source_literal"] == source for card in versions)
        assert versions[1]["acceptance_criteria"][0].startswith("original-")
        assert any("filtrar el resultado operativo" in item for item in versions[1]["acceptance_criteria"])
