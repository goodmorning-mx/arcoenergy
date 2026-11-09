import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, MetaData, String, Table, create_engine, inspect, select

from app.models import HistoryCard


def test_low_stock_migration_adds_owner_state_and_appends_card_version() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611090074_low_stock_responsible_push.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    old_inventory = Table("ae_inventory", MetaData(), Column("id", String(36), primary_key=True), Column("name", String(180)))
    old_inventory.create(engine)
    literal = "recibir notificaciones cuando un artículo esté agotándose o tenga existencia baja"
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-26", "version": 1, "iteration": "source",
            "stakeholder": "Contador", "source_literal": literal, "source_type": "Word",
            "source_reference": "source", "normalized_story": "Alertas de stock bajo",
            "acceptance_criteria": [], "unresolved_questions": ["Definir destinatarios."], "linked_cards": [],
            "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
            "source_attribution": "Mario", "source_confidence": "literal", "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_inventory")}
        assert {"restock_responsible_email", "low_stock_alert_active"} <= columns
        cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-26").order_by(HistoryCard.version)).mappings().all()
        assert [card["version"] for card in cards] == [1, 2]
        assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
        assert cards[1]["iteration"] == migration.ITERATION
        assert any("responsable de reposición" in criterion for criterion in cards[1]["acceptance_criteria"])
