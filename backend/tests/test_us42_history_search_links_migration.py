import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from app.models import HistoryCard


def test_history_search_migration_appends_us42_and_preserves_source() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic/versions/202611120141_us42_history_search_links.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app/history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-42")
    row = {**source, "id": str(uuid4()), "recorded_by": "source-import", "created_at": datetime.now(timezone.utc)}
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), row)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
            HistoryCard.acceptance_criteria).where(HistoryCard.story_id == "US-42").order_by(HistoryCard.version)).all()
    assert len(rows) == 2
    assert rows[0].source_literal == rows[1].source_literal == source["source_literal"]
    assert rows[1].iteration == migration.ITERATION
    assert any("buscar entre versiones" in item for item in rows[1].acceptance_criteria)
    assert any("relaciones entre la tarjeta y su fuente" in item for item in rows[1].acceptance_criteria)
