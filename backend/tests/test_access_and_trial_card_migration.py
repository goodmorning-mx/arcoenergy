import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_access_and_trial_migration_appends_versions_and_preserves_source_literals() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611060034_access_and_trial_mode_card_revisions.py"
    spec = importlib.util.spec_from_file_location("access_and_trial_card_revisions", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    sources = {story_id: f"fuente original {story_id}" for story_id in migration.UPDATES}
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert(), [
            {
                "id": f"source-{story_id}", "story_id": story_id, "version": 1,
                "iteration": "iteración inicial", "stakeholder": "Equipo",
                "source_literal": source, "source_type": "WhatsApp", "source_reference": "source.md",
                "normalized_story": "Accesos", "acceptance_criteria": [],
                "unresolved_questions": [], "linked_cards": [], "recorded_by": "stakeholder",
                "created_at": datetime.now(timezone.utc),
            }
            for story_id, source in sources.items()
        ])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
        assert len(rows) == len(sources) * 2
        for story_id, source in sources.items():
            versions = [row for row in rows if row["story_id"] == story_id]
            assert [row["version"] for row in versions] == [1, 2]
            assert versions[0]["source_literal"] == versions[1]["source_literal"] == source
            assert any("Nota del equipo basada en verificación de DEV" in criterion
                       for criterion in versions[1]["acceptance_criteria"])
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert len(connection.execute(select(table)).all()) == len(sources)
