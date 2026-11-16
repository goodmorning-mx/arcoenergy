import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import MetaData, create_engine, select

from app.models import HistoryCard
from app.product_api import HistoryCardInput


def load_migration():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611160155_story_card_requested_by.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_requested_by_migration_backfills_confirmed_authors_and_appends_iteration():
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), [
            {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "Importación",
                "stakeholder": stakeholder, "requested_by": "Por identificar", "source_literal": literal,
                "source_type": "WhatsApp", "source_reference": "history-cards.md#" + story_id,
                "normalized_story": literal, "acceptance_criteria": ["Criterio original"],
                "unresolved_questions": [], "linked_cards": [], "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            }
            for story_id, stakeholder, literal in (
                ("US-1", "Goito Profugo", "Solicitud de Goito."),
                ("US-15", "Mario Groso", "Solicitud de Mario."),
                ("US-33", "Contador sin identificar", "Transcripción sin autor."),
                ("US-42", "Dueño del producto", "Mantener el historial auditable."),
            )
        ])
        # Simulate the schema at the parent revision before requested_by existed.
        connection.exec_driver_sql("ALTER TABLE ae_history_cards DROP COLUMN requested_by")
        with Operations.context(MigrationContext.configure(connection)):
            load_migration().upgrade()
        table = HistoryCard.__table__
        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
    authors = {(row["story_id"], row["version"]): row["requested_by"] for row in rows}
    assert authors[("US-1", 1)] == "Goito Profugo"
    assert authors[("US-15", 1)] == "Mario Groso"
    assert authors[("US-33", 1)] == "Por identificar"
    assert authors[("US-42", 1)] == "Por identificar"
    latest = next(row for row in rows if row["story_id"] == "US-42" and row["version"] == 2)
    assert latest["source_literal"] == "Mantener el historial auditable."
    assert any("La atribución nominal de las transcripciones ASR" in str(question) for question in latest["unresolved_questions"])
    assert len(rows) == 5


def test_history_card_input_trims_requested_by_and_allows_unknown():
    values = {
        "story_id": "US-44", "version": 1, "iteration": "Iteración de prueba", "stakeholder": "Equipo",
        "source_literal": "Texto fuente.", "source_type": "WhatsApp", "source_reference": "history-cards.md#US-44",
        "normalized_story": "Capturar el requerimiento.",
    }
    assert HistoryCardInput(**values, requested_by="  Mario Groso  ").requested_by == "Mario Groso"
    assert HistoryCardInput(**values).requested_by == ""
