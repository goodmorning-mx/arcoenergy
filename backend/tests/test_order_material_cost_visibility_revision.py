import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_order_material_cost_revision_appends_to_us14_without_rewriting_source() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611100084_order_material_cost_visibility_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    records = json.loads((Path(__file__).parents[1] / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    source = next(row for row in records if row["story_id"] == "US-14")
    original_literal = source["source_literal"]
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), [{
            **row,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": now,
        } for row in records])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-14").order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert [row["version"] for row in versions] == [1, 2]
    assert all(row["source_literal"] == original_literal for row in versions)
    assert versions[1]["iteration"] == "Iteración 72 · privacidad de costos en órdenes de trabajo · 2026-11-10"
    assert any("disponibilidad" in item for item in versions[1]["acceptance_criteria"])
