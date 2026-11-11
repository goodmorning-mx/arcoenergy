import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_confirmed_quote_share_appends_us3_version_and_preserves_literal() -> None:
    base = Path(__file__).parents[1]
    migration_path = base / "alembic" / "versions" / "202611110105_us3_confirmed_whatsapp_share.py"
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    initial = next(row for row in json.loads((base / "app" / "history_card_initial.json").read_text()) if row["story_id"] == "US-3")
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), [{
            **initial, "id": str(uuid4()), "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        }])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-3").order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert versions[0]["source_literal"] == initial["source_literal"]
    assert versions[1]["source_literal"] == initial["source_literal"]
    assert versions[1]["version"] == 2
    assert versions[1]["iteration"] == migration.ITERATION
    assert any("confirmación de canal" in item for item in versions[1]["acceptance_criteria"])
    assert any("dispositivos reales" in item for item in versions[1]["unresolved_questions"])
