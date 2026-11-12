import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us13_dev_snapshot_verification_appends_without_rewriting_source() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611120137_us13_dev_snapshot_schedule_verification.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-13")
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            **source,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-13").order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == source["source_literal"]
    assert versions[-1]["iteration"] == migration.ITERATION
    assert any("no se registra como un respaldo ejecutado" in item for item in versions[-1]["acceptance_criteria"])
