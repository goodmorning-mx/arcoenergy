import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import MetaData, Table, create_engine, inspect, select

from app.models import HistoryCard, Quote


def test_drive_migration_adds_quote_file_id_and_appends_source_preserving_cards():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070050_quote_drive_storage.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    quote_columns = [column._copy() for column in Quote.__table__.columns if column.name != "drive_file_id"]
    Table("ae_quotes", MetaData(), *quote_columns).create(engine)
    HistoryCard.__table__.create(engine)
    literals = {"US-3": "Guardar la cotización en Drive y compartirla por WhatsApp", "US-13": "Que todo se vaya a un drive para almacenar todos los datos"}
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "Goito Profugo", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": literal, "normalized_story": "Documentos guardados en Drive",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "Goito Profugo", "source_confidence": "needs_validation",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assert "drive_file_id" in {column["name"] for column in inspect(connection).get_columns("ae_quotes")}
        for story_id, literal in literals.items():
            cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == story_id)
                                       .order_by(HistoryCard.version)).mappings().all()
            assert len(cards) == 2
            assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
            assert cards[1]["recorded_by"] == "system:implementation-iteration"
