import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select, text

from app.models import HistoryCard


def _load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_confirmed_followup_schema_and_card_revision_are_append_only():
    root = Path(__file__).parents[1]
    migration148 = _load(root / "alembic/versions/202611130148_us43_agentic_crm_operations.py")
    migration149 = _load(root / "alembic/versions/202611130149_us43_confirmed_agent_followups.py")
    records = json.loads((root / "app/history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    now = datetime.now(timezone.utc)

    with engine.begin() as connection:
        HistoryCard.__table__.create(connection)
        connection.execute(text("CREATE TABLE ae_followups (id VARCHAR(36) PRIMARY KEY)"))
        for source in records:
            connection.execute(HistoryCard.__table__.insert(), {
                **source, "id": str(uuid4()), "recorded_by": "source-import", "created_at": now,
            })
        source_us43 = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-43")).mappings().first()
        with Operations.context(MigrationContext.configure(connection)):
            migration148.upgrade()
            migration149.upgrade()

        versions = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-43").order_by(HistoryCard.version)).mappings().all()
        columns = {row["name"] for row in connection.execute(text("PRAGMA table_info(ae_followups)")).mappings()}
        intent_columns = {row["name"] for row in connection.execute(text("PRAGMA table_info(ae_agent_action_intents)")).mappings()}

    assert [row["version"] for row in versions] == [1, 2]
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == migration148.SOURCE_LITERAL
    assert "confirmación explícita" in " ".join(versions[1]["acceptance_criteria"])
    assert "agent_intent_id" in columns
    assert {"arguments_hash", "confirmation_token_hash", "status", "expires_at"} <= intent_columns
