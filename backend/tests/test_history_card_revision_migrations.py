import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, func, select
from sqlalchemy import inspect, text

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
    migration_019 = load_migration("202611060019_profitability_card_revisions.py")
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        with Operations.context(MigrationContext.configure(connection)):
            migration_012.upgrade()
            migration_014.upgrade()
            migration_016.upgrade()
            migration_019.upgrade()
        total = connection.scalar(select(func.count()).select_from(HistoryCard))
        source = connection.scalar(select(HistoryCard.source_literal).where(HistoryCard.story_id == "US-15", HistoryCard.version == 1))
        versions = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal)
            .where(HistoryCard.story_id == "US-15").order_by(HistoryCard.version)).all()
        linked_versions = connection.execute(select(HistoryCard.story_id, HistoryCard.version)
            .where(HistoryCard.story_id.in_(["US-17", "US-18", "US-21", "US-34", "US-35"]))).all()
        material_versions = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal)
            .where(HistoryCard.story_id == "US-9").order_by(HistoryCard.version)).all()
        report_versions = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal)
            .where(HistoryCard.story_id == "US-38").order_by(HistoryCard.version)).all()

    assert len(records) == 42
    assert total == 80
    assert len(versions) == 4
    assert all(version.source_literal == source for version in versions)
    assert versions[1].iteration == "Iteración 6 · ventas y órdenes · 2026-11-06"
    assert versions[2].iteration == "Iteración 7 · reserva y consumo de materiales · 2026-11-06"
    assert versions[3].iteration == "Iteración 8 · costeo preliminar por proyecto y mes · 2026-11-06"
    assert {story_id for story_id, _ in linked_versions} == {"US-17", "US-18", "US-21", "US-34", "US-35"}

    assert len(material_versions) == 2
    assert material_versions[0].source_literal == material_versions[1].source_literal
    assert material_versions[1].iteration == "Iteración 7 · reserva y consumo de materiales · 2026-11-06"
    assert len(report_versions) == 2
    assert report_versions[0].source_literal == report_versions[1].source_literal
    assert report_versions[1].iteration == "Iteración 8 · costeo preliminar por proyecto y mes · 2026-11-06"


def test_stock_notification_migration_appends_us26_history_revision() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    records = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    migration = load_migration("202611080063_stock_low_notification_card_revision.py")
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        source = connection.scalar(select(HistoryCard.source_literal).where(HistoryCard.story_id == "US-26", HistoryCard.version == 1))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
            HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions)
            .where(HistoryCard.story_id == "US-26").order_by(HistoryCard.version)).all()

    assert len(versions) == 2
    assert all(version.source_literal == source for version in versions)
    assert versions[1].iteration == "Iteración 52 · avisos de stock bajo en PWA · 2026-11-08"
    assert any("permiso de notificaciones" in item for item in versions[1].acceptance_criteria)
    assert any("aplicación cerrada" in item for item in versions[1].unresolved_questions)


def test_purchase_correction_migration_adds_schema_and_appends_source_linked_versions() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    records = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    migration = load_migration("202611080064_purchase_correction_history.py")
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        connection.execute(text("ALTER TABLE ae_purchase_lines DROP COLUMN previous_unit_cost"))
        source = connection.scalar(select(HistoryCard.source_literal).where(HistoryCard.story_id == "US-36", HistoryCard.version == 1))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_purchase_lines")}
        corrections = inspect(connection).get_columns("ae_purchase_corrections")
        version = connection.execute(select(HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
            HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions)
            .where(HistoryCard.story_id == "US-36").order_by(HistoryCard.version.desc())).first()

    assert "previous_unit_cost" in columns
    assert {column["name"] for column in corrections} >= {"purchase_id", "reason", "amount"}
    assert version is not None and version.version == 2
    assert version.iteration == "Iteración 53 · corrección de compras antes de movimiento de almacén · 2026-11-08"
    assert version.source_literal == source
    assert any("pagos activos" in item for item in version.unresolved_questions)
