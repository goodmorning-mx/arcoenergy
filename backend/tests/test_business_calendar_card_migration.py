import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_business_calendar_migration_appends_versions_and_preserves_source_literals() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611110093_business_calendar_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((Path(__file__).parents[1] / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    targets = {"US-11", "US-16", "US-17", "US-18", "US-31", "US-34"}
    initial = [row for row in records if row["story_id"] in targets]
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), [{
            **row,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        } for row in records])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        for story_id in targets:
            versions = connection.execute(
                select(HistoryCard.__table__)
                .where(HistoryCard.story_id == story_id)
                .order_by(HistoryCard.version)
            ).mappings().all()
            source = next(row["source_literal"] for row in initial if row["story_id"] == story_id)
            assert len(versions) == 2
            assert versions[0]["source_literal"] == source
            assert versions[1]["source_literal"] == source
            assert versions[1]["version"] == 2
            assert versions[1]["iteration"] == migration.ITERATION
