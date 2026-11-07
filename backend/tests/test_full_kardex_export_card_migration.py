import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_full_kardex_export_migration_appends_us27_and_keeps_original_source() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611060037_full_kardex_export_card_revision.py"
    spec = importlib.util.spec_from_file_location("full_kardex_export_card_revision", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    source = "Filtrar movimientos por producto y periodo."
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), {
            "id": "source", "story_id": "US-27", "version": 1, "iteration": "inicial",
            "stakeholder": "Contador", "source_literal": source, "source_type": "Documento",
            "source_reference": "contador.pdf", "normalized_story": "Kardex", "acceptance_criteria": [],
            "unresolved_questions": [], "linked_cards": [], "recorded_by": "stakeholder",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.version)).mappings().all()
        assert [row["version"] for row in rows] == [1, 2]
        assert rows[1]["source_literal"] == source
        assert "todas las páginas filtradas" in rows[1]["acceptance_criteria"][-1]
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert len(connection.execute(select(table)).all()) == 1
