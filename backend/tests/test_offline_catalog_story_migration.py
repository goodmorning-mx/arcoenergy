import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_offline_catalog_revision_preserves_original_story_source() -> None:
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location(
        "offline_catalog_story_revision",
        root / "alembic" / "versions" / "202611060031_offline_catalog_story_revision.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    literal = "Los códigos de barras identifican el artículo desde la aplicación móvil."
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert().values(
            id="source", story_id="US-28", version=1, iteration="iteración 1", stakeholder="Instalador",
            source_literal=literal, source_type="Conversación", source_reference="source.md",
            normalized_story="Identificar artículos", acceptance_criteria=[], unresolved_questions=[],
            linked_cards=[], recorded_by="stakeholder", created_at=datetime.now(timezone.utc),
        ))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.version)).mappings().all()
        assert [row["version"] for row in rows] == [1, 2]
        assert all(row["source_literal"] == literal for row in rows)
        assert rows[1]["linked_cards"] == ["US-10", "US-40", "US-9"]
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert len(connection.execute(select(table)).all()) == 1
