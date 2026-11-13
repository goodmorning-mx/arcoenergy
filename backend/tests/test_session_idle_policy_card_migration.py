import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_session_idle_policy_appends_us14_us40_without_changing_source_literals() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611130145_us14_us40_session_idle_policy.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((Path(__file__).parents[1] / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    sources = {row["story_id"]: row for row in records if row["story_id"] in {"US-14", "US-40"}}
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__

    with engine.begin() as connection:
        table.create(connection)
        for story_id, source in sources.items():
            connection.execute(table.insert(), {
                **source, "id": str(uuid4()), "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        for story_id, source in sources.items():
            versions = connection.execute(
                select(table).where(table.c.story_id == story_id).order_by(table.c.version)
            ).mappings().all()
            assert len(versions) == 2
            assert versions[0]["source_literal"] == versions[1]["source_literal"] == source["source_literal"]
            assert versions[1]["iteration"] == migration.ITERATION
            assert any("36,500 días" in criterion for criterion in versions[1]["acceptance_criteria"])
            assert not any("30 días" in question for question in versions[1]["unresolved_questions"])
