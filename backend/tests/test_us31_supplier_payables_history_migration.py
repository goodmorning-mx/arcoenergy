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


def test_us31_supplier_payables_iteration_preserves_original_source() -> None:
    records = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    path = ROOT / "alembic" / "versions" / "202611110116_us31_supplier_payables_coverage.py"
    spec = importlib.util.spec_from_file_location("us31_supplier_payables_coverage", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        source = connection.scalar(select(HistoryCard.source_literal).where(
            HistoryCard.story_id == "US-31", HistoryCard.version == 1,
        ))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(
            HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
            HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions,
        ).where(HistoryCard.story_id == "US-31").order_by(HistoryCard.version)).all()

    assert len(versions) == 2
    assert all(row.source_literal == source for row in versions)
    assert versions[1].iteration == "Iteración 104 · compras, saldos y pagos a proveedores · 2026-11-11"
    assert any("aumenta su saldo pendiente" in item for item in versions[1].acceptance_criteria)
    assert any("conciliación bancaria" in item for item in versions[1].unresolved_questions)
