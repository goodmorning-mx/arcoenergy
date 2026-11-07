import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_inventory_qr_migration_appends_us20_and_us28_without_source_edits() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611060036_inventory_qr_label_card_revisions.py"
    spec = importlib.util.spec_from_file_location("inventory_qr_label_card_revisions", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    source_literals = {story_id: f"historia fuente {story_id}" for story_id in migration.UPDATES}
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), [
            {"id": f"source-{story_id}", "story_id": story_id, "version": 1, "iteration": "inicial",
             "stakeholder": "Almacén", "source_literal": literal, "source_type": "Documento",
             "source_reference": "source.docx", "normalized_story": "Escaneo de almacén",
             "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
             "recorded_by": "stakeholder", "created_at": datetime.now(timezone.utc)}
            for story_id, literal in source_literals.items()
        ])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
        assert len(rows) == 4
        for story_id, literal in source_literals.items():
            versions = [row for row in rows if row["story_id"] == story_id]
            assert [row["version"] for row in versions] == [1, 2]
            assert versions[0]["source_literal"] == versions[1]["source_literal"] == literal
            assert "QR" in versions[1]["acceptance_criteria"][-1]
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert len(connection.execute(select(table)).all()) == 2
