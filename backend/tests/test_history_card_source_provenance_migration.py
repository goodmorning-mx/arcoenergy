import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, DateTime, Integer, JSON, MetaData, String, Table, Text, create_engine, inspect, select

from app.models import HistoryCard


def load_migration():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070046_history_card_source_provenance.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
    return migration


def insert_old_row(connection, table):
    connection.execute(table.insert(), {
        "id": str(uuid4()), "story_id": "US-42", "version": 1, "iteration": "source-import",
        "stakeholder": "Stakeholder", "source_literal": "Texto fuente", "source_type": "WhatsApp",
        "source_reference": "sources/chat.md#message-7", "normalized_story": "Capturar el hallazgo",
        "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
        "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
    })


def test_migration_adds_provenance_columns_and_marks_reconstructed_metadata():
    engine = create_engine("sqlite://")
    old = Table("ae_history_cards", MetaData(),
        Column("id", String, primary_key=True), Column("story_id", String, nullable=False),
        Column("version", Integer, nullable=False), Column("iteration", String, nullable=False),
        Column("stakeholder", String, nullable=False), Column("source_literal", Text, nullable=False),
        Column("source_type", String, nullable=False), Column("source_reference", Text),
        Column("normalized_story", Text, nullable=False), Column("acceptance_criteria", JSON),
        Column("unresolved_questions", JSON), Column("linked_cards", JSON), Column("recorded_by", String, nullable=False),
        Column("created_at", DateTime(timezone=True)))
    old.create(engine)
    migration = load_migration()
    with engine.begin() as connection:
        insert_old_row(connection, old)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        history = Table("ae_history_cards", MetaData(), autoload_with=connection)
        row = connection.execute(select(history).where(history.c.version == 1)).mappings().one()
        versions = connection.execute(select(history.c.version, history.c.source_literal)
                                      .where(history.c.story_id == "US-42")
                                      .order_by(history.c.version)).all()
    assert row["source_artifact"]["artifacts"][0]["reference"] == "sources/chat.md#message-7"
    assert row["source_attribution"] == "Stakeholder"
    assert row["source_language"] == "es"
    assert row["source_confidence"] == "needs_validation"
    assert row["source_links"] == [{"artifact_index": 0, "relation": "reconstruction", "location": ""}]
    assert [version for version, _ in versions] == [1, 2]
    assert versions[0].source_literal == versions[1].source_literal == "Texto fuente"


def test_migration_backfills_rows_when_initial_model_already_created_new_columns():
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    migration = load_migration()
    with engine.begin() as connection:
        insert_old_row(connection, HistoryCard.__table__)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_history_cards")}
        row = connection.execute(select(HistoryCard.__table__).where(HistoryCard.__table__.c.version == 1)).mappings().one()
        versions = connection.execute(select(HistoryCard.__table__.c.version, HistoryCard.__table__.c.source_literal)
                                      .where(HistoryCard.__table__.c.story_id == "US-42")
                                      .order_by(HistoryCard.__table__.c.version)).all()
    assert {"source_artifact", "source_language", "source_attribution", "source_occurred_at", "source_confidence", "source_links"} <= columns
    assert row["source_artifact"]["artifacts"][0]["artifact_type"] == "WhatsApp"
    assert row["source_attribution"] == "Stakeholder"
    assert row["source_confidence"] == "needs_validation"
    assert [version for version, _ in versions] == [1, 2]
    assert versions[0].source_literal == versions[1].source_literal == "Texto fuente"
