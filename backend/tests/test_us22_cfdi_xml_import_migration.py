import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us22_cfdi_iteration_appends_version_and_preserves_source_literal() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611110134_us22_cfdi_xml_import_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-22")
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        original = {
            **source,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        }
        connection.execute(HistoryCard.__table__.insert(), original)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.story_id == "US-22")
            .order_by(HistoryCard.version)
        ).mappings().all()

    assert len(rows) == 2
    assert rows[0]["source_literal"] == rows[1]["source_literal"] == source["source_literal"]
    assert rows[-1]["iteration"] == migration.ITERATION
    assert any("CFDI XML 3.3/4.0" in item for item in rows[-1]["acceptance_criteria"])
    assert any("Contabilidad" in item for item in rows[-1]["unresolved_questions"])
