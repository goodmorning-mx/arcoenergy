import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, select

from app.models import Base, HistoryCard, ProfitabilityAdjustment


def test_adjustment_migration_creates_append_only_table_and_appends_story_version() -> None:
    root = Path(__file__).parents[1]
    migration_path = root / "alembic" / "versions" / "202611100079_profitability_adjustments.py"
    spec = importlib.util.spec_from_file_location("profitability_adjustments_migration", migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE ae_profitability_adjustments")
        records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc)
        for row in records:
            row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
        connection.execute(HistoryCard.__table__.insert(), records)
        original_source = connection.scalar(select(HistoryCard.source_literal).where(HistoryCard.story_id == "US-38", HistoryCard.version == 1))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(HistoryCard).where(HistoryCard.story_id == "US-38").order_by(HistoryCard.version)).mappings().all()
        assert inspect(connection).has_table(ProfitabilityAdjustment.__tablename__)
        assert {index["name"] for index in inspect(connection).get_indexes(ProfitabilityAdjustment.__tablename__)} >= {
            "ix_ae_profitability_adjustments_installation_id", "ix_ae_profitability_adjustments_reversal_of_id",
        }

    assert len(versions) == 2
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == original_source
    assert versions[1]["iteration"] == "Iteración 67 · devoluciones y bonificaciones en resultado · 2026-11-10"
    assert any("devoluciones y bonificaciones" in criterion for criterion in versions[1]["acceptance_criteria"])
