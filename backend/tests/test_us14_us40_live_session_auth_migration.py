import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def _load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_live_session_verification_is_appended_and_preserves_source_cards():
    root = Path(__file__).parents[1]
    migration = _load(root / "alembic/versions/202611140153_us14_us40_live_session_auth.py")
    records = json.loads((root / "app/history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    now = datetime.now(timezone.utc)
    story_ids = ("US-14", "US-40", "US-42")

    with engine.begin() as connection:
        HistoryCard.__table__.create(connection)
        for source in records:
            connection.execute(HistoryCard.__table__.insert(), {
                **source, "id": str(uuid4()), "recorded_by": "source-import", "created_at": now,
            })
        before = {
            story_id: connection.execute(
                select(HistoryCard.__table__).where(HistoryCard.story_id == story_id).order_by(HistoryCard.version.desc())
            ).mappings().first()
            for story_id in story_ids
        }
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        latest = {
            story_id: connection.execute(
                select(HistoryCard.__table__).where(HistoryCard.story_id == story_id).order_by(HistoryCard.version.desc())
            ).mappings().first()
            for story_id in story_ids
        }

    for story_id in story_ids:
        assert latest[story_id]["version"] == before[story_id]["version"] + 1
        assert latest[story_id]["source_literal"] == before[story_id]["source_literal"]
        assert migration.UPDATES[story_id][0] in latest[story_id]["acceptance_criteria"]
        assert migration.UPDATES[story_id][1] in latest[story_id]["unresolved_questions"]
    assert "36,500" in " ".join(latest["US-14"]["acceptance_criteria"])
    assert "cerrar" in " ".join(latest["US-40"]["acceptance_criteria"]).lower()
