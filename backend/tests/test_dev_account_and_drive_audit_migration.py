import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_dev_account_and_drive_audit_appends_versions_without_personal_data() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611110100_dev_account_and_drive_audit.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((Path(__file__).parents[1] / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        for story_id in migration.STORIES:
            source = next(row for row in records if row["story_id"] == story_id)
            connection.execute(HistoryCard.__table__.insert(), {
                **source,
                "id": str(uuid4()),
                "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(HistoryCard.__table__)).mappings().all()
        assert len(rows) == 8
        for story_id in migration.STORIES:
            versions = [row for row in rows if row["story_id"] == story_id]
            assert len(versions) == 2
            assert versions[0]["source_literal"] == versions[1]["source_literal"]
            assert versions[1]["iteration"] == migration.ITERATION
        added_text = " ".join(
            " ".join(criteria + questions)
            for criteria, questions in migration.STORIES.values()
        )
        assert "@" not in added_text
