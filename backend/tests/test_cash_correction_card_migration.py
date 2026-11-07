import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import Base, HistoryCard


ROOT = Path(__file__).resolve().parents[1]


def test_cash_correction_revision_appends_without_rewriting_literal_source() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    cards = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for card in cards:
        card.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), cards)
        path = ROOT / "alembic/versions/202611070059_cash_correction_reason_card_revision.py"
        spec = importlib.util.spec_from_file_location("cash_correction_reason_revision", path)
        assert spec and spec.loader
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(
            HistoryCard.source_literal, HistoryCard.version, HistoryCard.iteration, HistoryCard.acceptance_criteria,
        ).where(HistoryCard.story_id == "US-36").order_by(HistoryCard.version)).all()
    assert len(versions) == 2
    assert versions[0].source_literal == versions[1].source_literal
    assert versions[1].version == 2
    assert versions[1].iteration == "Iteración 48 · correcciones de caja con motivo y origen protegido · 2026-11-07"
    assert any("exigen motivo" in criterion for criterion in versions[1].acceptance_criteria)
