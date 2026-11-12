import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_quote_customer_reuse_appends_us1_and_us3_without_rewriting_sources() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611120138_us1_pwa_quote_customer_reuse.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        rows = [row for row in records if row["story_id"] in {"US-1", "US-3"}]
        for row in rows:
            row.update(id=str(uuid4()), recorded_by="source-import", created_at=datetime.now(timezone.utc))
        connection.execute(HistoryCard.__table__.insert(), rows)
        original_sources = {
            row["story_id"]: row["source_literal"] for row in rows
        }
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.story_id, HistoryCard.version, HistoryCard.iteration,
                   HistoryCard.source_literal, HistoryCard.acceptance_criteria)
            .where(HistoryCard.story_id.in_(["US-1", "US-3"]))
            .order_by(HistoryCard.story_id, HistoryCard.version)
        ).all()

    assert len(versions) == 4
    for story_id in ("US-1", "US-3"):
        story_versions = [row for row in versions if row.story_id == story_id]
        assert story_versions[0].source_literal == story_versions[1].source_literal == original_sources[story_id]
        assert story_versions[1].iteration == migration.ITERATION
    assert any("reintento reutiliza la ficha creada" in item for item in versions[1].acceptance_criteria)
    assert any("se limpia el folio/PDF anterior" in item for item in versions[3].acceptance_criteria)
