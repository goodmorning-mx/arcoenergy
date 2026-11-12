import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_dev_quote_release_migration_appends_evidence_to_three_cards() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611120139_us13_quote_release_dev_verification.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    selected = [row for row in records if row["story_id"] in {"US-1", "US-3", "US-13", "US-14", "US-40"}]
    sources = {row["story_id"]: row["source_literal"] for row in selected}
    for row in selected:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=datetime.now(timezone.utc))
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), selected)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.story_id, HistoryCard.version, HistoryCard.iteration,
                   HistoryCard.source_literal, HistoryCard.acceptance_criteria,
                   HistoryCard.unresolved_questions)
            .where(HistoryCard.story_id.in_(list(sources)))
            .order_by(HistoryCard.story_id, HistoryCard.version)
        ).all()
    assert len(versions) == 10
    for story_id, source in sources.items():
        rows = [row for row in versions if row.story_id == story_id]
        assert rows[0].source_literal == rows[1].source_literal == source
        assert rows[1].iteration == migration.ITERATION
    us13 = next(row for row in versions if row.story_id == "US-13" and row.version == 2)
    assert any("cinco servicios DEV" in item for item in us13.acceptance_criteria)
    assert any("no acredita una carga empresarial JSON" in item for item in us13.unresolved_questions)
    us14 = next(row for row in versions if row.story_id == "US-14" and row.version == 2)
    assert any("LoginScreen" in item for item in us14.acceptance_criteria)
    us40 = next(row for row in versions if row.story_id == "US-40" and row.version == 2)
    assert any("formulario de acceso" in item for item in us40.acceptance_criteria)
