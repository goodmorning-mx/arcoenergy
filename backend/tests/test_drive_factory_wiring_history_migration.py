import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_drive_factory_wiring_appends_us3_us10_us13_without_changing_source():
    root = Path(__file__).parents[1]
    migration_path = root / "alembic/versions/202611120142_us3_us10_us13_drive_factory_wiring.py"
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    sources = json.loads((root / "app/history_card_initial.json").read_text(encoding="utf-8"))
    selected = [row for row in sources if row["story_id"] in {"US-3", "US-10", "US-13"}]
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        for source in selected:
            connection.execute(HistoryCard.__table__.insert(), {
                **source, "id": str(uuid4()), "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.__table__.c.story_id.in_(["US-3", "US-10", "US-13"]))
            .order_by(HistoryCard.__table__.c.story_id, HistoryCard.__table__.c.version)
        ).mappings().all()

    assert len(rows) == 6
    by_story = {}
    for row in rows:
        by_story.setdefault(row["story_id"], []).append(row)
    assert set(by_story) == {"US-3", "US-10", "US-13"}
    for story_id, versions in by_story.items():
        assert [row["version"] for row in versions] == [1, 2]
        assert versions[0]["source_literal"] == versions[1]["source_literal"]
        assert versions[1]["iteration"] == migration.ITERATION
        assert versions[1]["acceptance_criteria"] != versions[0]["acceptance_criteria"]
        assert versions[1]["unresolved_questions"] != versions[0]["unresolved_questions"]
