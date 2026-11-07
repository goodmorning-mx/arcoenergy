import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import MetaData, Table, create_engine, inspect, select

from app.models import HistoryCard, Purchase


def test_purchase_invoice_migration_preserves_original_story_sources():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070054_purchase_invoice_private_storage.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    new_columns = {"invoice_drive_file_id", "invoice_filename", "invoice_content_type", "invoice_updated_at"}
    purchase_columns = [column._copy() for column in Purchase.__table__.columns if column.name not in new_columns]
    Table("ae_purchases", MetaData(), *purchase_columns).create(engine)
    HistoryCard.__table__.create(engine)
    literals = {
        "US-13": "Que todo se vaya a un drive para almacenar todos los datos",
        "US-21": "Las compras de material",
        "US-22": "Como responsable de almacén/contador, quiero cargar una factura (archivo/XML o fotografía) para facilitar el registro de los artículos recibidos.",
    }
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "stakeholder", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": literal, "normalized_story": "captura y respaldo de compra",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "stakeholder", "source_confidence": "literal",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_purchases")}
        assert {"invoice_drive_file_id", "invoice_filename", "invoice_content_type", "invoice_updated_at"} <= columns
        for story_id, literal in literals.items():
            cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == story_id)
                                       .order_by(HistoryCard.version)).mappings().all()
            assert len(cards) == 2
            assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
            assert cards[1]["iteration"] == migration.ITERATION

