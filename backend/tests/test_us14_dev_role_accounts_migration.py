import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_dev_account_role_check_appends_us14_without_changing_source_literal() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611130147_us14_dev_role_accounts.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((Path(__file__).parents[1] / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-14")
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__

    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), {
            **source, "id": str(uuid4()), "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        versions = connection.execute(
            select(table).where(table.c.story_id == "US-14").order_by(table.c.version)
        ).mappings().all()
        assert len(versions) == 2
        assert versions[0]["source_literal"] == versions[1]["source_literal"] == source["source_literal"]
        assert versions[1]["iteration"] == migration.ITERATION
        assert migration.ACCEPTANCE_CRITERION in versions[1]["acceptance_criteria"]
        assert versions[1]["version"] == versions[0]["version"] + 1
