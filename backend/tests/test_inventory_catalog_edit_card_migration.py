import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_inventory_catalog_edit_migration_appends_revision_without_rewriting_source():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070045_inventory_catalog_edit_card.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literal = "Nosotros como administradores llevar el control de materiales, costos directos."
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-20", "version": 3, "iteration": "original",
            "stakeholder": "Mario Groso", "source_type": "Word", "source_reference": "docx:seccion-inventario",
            "source_literal": literal, "normalized_story": "Controlar catálogo de materiales",
            "acceptance_criteria": ["Administrar materiales"], "unresolved_questions": [], "linked_cards": [],
            "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-20")
                                   .order_by(HistoryCard.version)).mappings().all()
    assert [card["version"] for card in cards] == [3, 4]
    assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
    assert any("existencias directamente" in criterion for criterion in cards[1]["acceptance_criteria"])
