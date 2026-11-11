import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import Base, HistoryCard


ROOT = Path(__file__).resolve().parents[1]


def test_costing_iteration_appends_us12_us38_without_changing_source_literals() -> None:
    records = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    path = ROOT / "alembic" / "versions" / "202611110117_us12_us38_preliminary_costing.py"
    spec = importlib.util.spec_from_file_location("us12_us38_costing", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        sources = dict(connection.execute(select(HistoryCard.story_id, HistoryCard.source_literal).where(
            HistoryCard.story_id.in_(migration.REVISIONS), HistoryCard.version == 1,
        )).all())
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(
            HistoryCard.story_id, HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
            HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions,
        ).where(HistoryCard.story_id.in_(migration.REVISIONS)).order_by(HistoryCard.story_id, HistoryCard.version)).all()

    assert len(versions) == 4
    for story_id in migration.REVISIONS:
        rows = [row for row in versions if row.story_id == story_id]
        assert rows[-1].version == 2
        assert all(row.source_literal == sources[story_id] for row in rows)
        assert rows[-1].iteration == "Iteración 105 · costos directos y resultado preliminar · 2026-11-11"
    assert any("no inventa un total" in item for item in next(row for row in versions if row.story_id == "US-12" and row.version == 2).acceptance_criteria)
    assert any("no se presenta como estado financiero completo" in item for item in next(row for row in versions if row.story_id == "US-38" and row.version == 2).acceptance_criteria)
