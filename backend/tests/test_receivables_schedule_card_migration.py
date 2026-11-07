import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_receivables_schedule_revision_preserves_source_literal() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611060041_receivables_schedule_card_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    source_literal = "Mario pide mensajes sobre pagos próximos, del día o atrasados."
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-11", "version": 1, "iteration": "initial",
            "stakeholder": "Goito", "source_type": "WhatsApp", "source_reference": "source",
            "source_literal": source_literal, "normalized_story": "Administrar cobranza",
            "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
            "recorded_by": "source-import", "created_at": now,
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-11").order_by(HistoryCard.version)).mappings().all()

    assert [card["version"] for card in versions] == [1, 2]
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == source_literal
    assert any("próximos siete días" in item for item in versions[1]["acceptance_criteria"])
