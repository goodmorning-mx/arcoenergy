import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us14_protected_login_migration_appends_version_and_preserves_source() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611110133_us14_protected_login_surfaces.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-14")
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        imported = {
            **source,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        }
        connection.execute(HistoryCard.__table__.insert(), imported)
        previous = {
            **imported,
            "id": str(uuid4()),
            "version": 2,
            "iteration": "Iteración previa",
            "acceptance_criteria": [*imported["acceptance_criteria"], "Criterio previo"],
        }
        connection.execute(HistoryCard.__table__.insert(), previous)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.story_id == "US-14")
            .order_by(HistoryCard.version)
        ).mappings().all()

    assert len(rows) == 3
    assert all(row["source_literal"] == source["source_literal"] for row in rows)
    assert rows[-1]["version"] == 3
    assert rows[-1]["iteration"] == migration.ITERATION
    assert any("/app/" in item and "/crm/" in item for item in rows[-1]["acceptance_criteria"])
    assert any("cuentas reales" in item for item in rows[-1]["unresolved_questions"])
