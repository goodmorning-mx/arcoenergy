import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from app.models import HistoryCard


def test_login_chrome_migration_appends_both_cards_and_preserves_sources() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic/versions/202611120140_us14_us40_login_chrome_verification.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app/history_card_initial.json").read_text(encoding="utf-8"))
    rows = [row for row in records if row["story_id"] in {"US-14", "US-40"}]
    sources = {row["story_id"]: row["source_literal"] for row in rows}
    for row in rows:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=datetime.now(timezone.utc))
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), rows)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        result = connection.execute(select(HistoryCard.story_id, HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal, HistoryCard.acceptance_criteria).where(HistoryCard.story_id.in_(sources))).all()
    assert len(result) == 4
    for story_id, source in sources.items():
        versions = [row for row in result if row.story_id == story_id]
        assert len(versions) == 2
        assert versions[0].source_literal == versions[1].source_literal == source
        assert versions[1].iteration == migration.ITERATION
    assert any("43245435339" in item for row in result if row.story_id == "US-14" for item in row.acceptance_criteria)
    assert any("43245435339" in item for row in result if row.story_id == "US-40" for item in row.acceptance_criteria)
