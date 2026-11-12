import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us14_client_provisioning_iteration_appends_and_preserves_original_story() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611110135_us14_client_account_provisioning.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-14")
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        original = {
            **source,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        }
        connection.execute(HistoryCard.__table__.insert(), original)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.story_id == "US-14")
            .order_by(HistoryCard.version)
        ).mappings().all()

    assert len(rows) == 2
    assert rows[0]["source_literal"] == rows[1]["source_literal"] == source["source_literal"]
    assert rows[-1]["iteration"] == migration.ITERATION
    assert any("correo de la cuenta coincide" in item for item in rows[-1]["acceptance_criteria"])
