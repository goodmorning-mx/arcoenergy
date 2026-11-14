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


def test_us39_session_history_is_appended_without_replacing_source():
    root = Path(__file__).parents[1]
    migration = _load(root / "alembic/versions/202611130151_us39_session_agent_history.py")
    records = json.loads((root / "app/history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    now = datetime.now(timezone.utc)

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
            for story_id in ("US-39", "US-42")
        }
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-39").order_by(HistoryCard.version)
        ).mappings().all()
        audit_versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-42").order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == before["US-39"]["source_literal"]
    assert "sessionStorage" in " ".join(versions[1]["acceptance_criteria"])
    assert "reinicio de API" in " ".join(versions[1]["unresolved_questions"])
    assert audit_versions[-1]["version"] == before["US-42"]["version"] + 1
    assert audit_versions[-1]["source_literal"] == before["US-42"]["source_literal"]
