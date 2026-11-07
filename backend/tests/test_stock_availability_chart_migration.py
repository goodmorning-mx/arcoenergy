import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_stock_chart_revision_appends_us19_and_us29_without_changing_sources() -> None:
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location(
        "stock_availability_chart_card_revisions",
        root / "alembic" / "versions" / "202611060033_stock_availability_chart_card_revisions.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    sources = {story_id: f"fuente original {story_id}" for story_id in migration.UPDATES}
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), [
            {"id": f"source-{story_id}", "story_id": story_id, "version": 1, "iteration": "iteración 1",
             "stakeholder": "Contador", "source_literal": source, "source_type": "Documento",
             "source_reference": "source.docx", "normalized_story": "Reporte", "acceptance_criteria": [],
             "unresolved_questions": [], "linked_cards": [], "recorded_by": "stakeholder",
             "created_at": datetime.now(timezone.utc)}
            for story_id, source in sources.items()
        ])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
        assert len(rows) == 4
        for story_id, source in sources.items():
            versions = [row for row in rows if row["story_id"] == story_id]
            assert [row["version"] for row in versions] == [1, 2]
            assert versions[0]["source_literal"] == versions[1]["source_literal"] == source
            assert versions[1]["unresolved_questions"]
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        remaining = connection.execute(select(table)).mappings().all()
        assert len(remaining) == 2
