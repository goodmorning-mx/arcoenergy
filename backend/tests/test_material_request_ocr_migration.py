import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import Base, HistoryCard


def test_material_request_ocr_appends_us25_version_and_preserves_source():
    root = Path(__file__).resolve().parents[1]
    migration_path = root / "alembic" / "versions" / "202611110106_us25_material_request_ocr.py"
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    original = next(row for row in records if row["story_id"] == "US-25")
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
                   HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions)
            .where(HistoryCard.story_id == "US-25").order_by(HistoryCard.version)
        ).all()

    assert len(versions) == 2
    assert versions[0].source_literal == original["source_literal"]
    assert versions[1].version == 2
    assert versions[1].iteration == "Iteración 94 · lectura asistida de solicitud de materiales · 2026-11-11"
    assert versions[1].source_literal == original["source_literal"]
    assert any("no confirma cantidades" in item for item in versions[1].acceptance_criteria)
    assert any("formato real del almacén" in item for item in versions[1].unresolved_questions)
