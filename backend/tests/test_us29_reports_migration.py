import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import Base, HistoryCard


def test_operations_reports_append_us29_version_and_preserve_source():
    root = Path(__file__).resolve().parents[1]
    migration_path = root / "alembic" / "versions" / "202611110108_us29_operations_reports.py"
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    original = next(row for row in records if row["story_id"] == "US-29")
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
                   HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions)
            .where(HistoryCard.story_id == "US-29").order_by(HistoryCard.version)
        ).all()

    assert len(versions) == 2
    assert versions[0].source_literal == original["source_literal"]
    assert versions[1].version == 2
    assert versions[1].iteration == "Iteración 96 · cobertura de reportes operativos · 2026-11-11"
    assert versions[1].source_literal == original["source_literal"]
    assert any("gráfica de disponibilidad" in item for item in versions[1].acceptance_criteria)
    assert any("costos unitarios" in item and "permisos" in item for item in versions[1].acceptance_criteria)
    assert any("US-12 y US-38" in item for item in versions[1].unresolved_questions)
