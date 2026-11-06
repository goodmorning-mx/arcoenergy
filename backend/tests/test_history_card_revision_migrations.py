import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, func, select

from app.models import Base, HistoryCard


ROOT = Path(__file__).resolve().parents[1]


def load_migration(filename: str):
    spec = importlib.util.spec_from_file_location(filename, ROOT / "alembic" / "versions" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_accounting_and_sales_iterations_append_versions_without_changing_sources() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    records = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)

    migration_012 = load_migration("202611060012_accounting_card_revisions.py")
    migration_014 = load_migration("202611060014_sales_card_revisions.py")
    migration_016 = load_migration("202611060016_work_order_material_revisions.py")
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        with Operations.context(MigrationContext.configure(connection)):
            migration_012.upgrade()
            migration_014.upgrade()
            migration_016.upgrade()
        total = connection.scalar(select(func.count()).select_from(HistoryCard))
        source = connection.scalar(select(HistoryCard.source_literal).where(HistoryCard.story_id == "US-15", HistoryCard.version == 1))
        versions = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal)
            .where(HistoryCard.story_id == "US-15").order_by(HistoryCard.version)).all()
        linked_versions = connection.execute(select(HistoryCard.story_id, HistoryCard.version)
            .where(HistoryCard.story_id.in_(["US-17", "US-18", "US-21", "US-34", "US-35"]))).all()
        material_versions = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal)
            .where(HistoryCard.story_id == "US-9").order_by(HistoryCard.version)).all()

    assert len(records) == 42
    assert total == 73
    assert len(versions) == 3
    assert all(version.source_literal == source for version in versions)
    assert versions[1].iteration == "Iteración 6 · ventas y órdenes · 2026-11-06"
    assert versions[2].iteration == "Iteración 7 · reserva y consumo de materiales · 2026-11-06"
    assert {story_id for story_id, _ in linked_versions} == {"US-17", "US-18", "US-21", "US-34", "US-35"}

    assert len(material_versions) == 2
    assert material_versions[0].source_literal == material_versions[1].source_literal
    assert material_versions[1].iteration == "Iteración 7 · reserva y consumo de materiales · 2026-11-06"
