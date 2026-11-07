import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, Text, create_engine, select


def test_offline_checklist_revision_appends_story_without_rewriting_source() -> None:
    root = Path(__file__).parents[1]
    spec = importlib.util.spec_from_file_location(
        "offline_checklist_card_revision",
        root / "alembic" / "versions" / "202611060028_offline_field_checklist_card_revision.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    metadata = MetaData()
    history = Table(
        "ae_history_cards", metadata,
        Column("id", String(36), primary_key=True), Column("story_id", String(30), nullable=False),
        Column("version", Integer, nullable=False), Column("iteration", String(80), nullable=False),
        Column("stakeholder", String(180), nullable=False), Column("source_literal", Text, nullable=False),
        Column("source_type", String(40), nullable=False), Column("source_reference", Text),
        Column("normalized_story", Text, nullable=False), Column("acceptance_criteria", JSON),
        Column("unresolved_questions", JSON), Column("linked_cards", JSON),
        Column("recorded_by", String(180), nullable=False), Column("created_at", DateTime(timezone=True)),
    )
    sources = {
        "US-14": "Si todo fuera desde una app, cada usuario tendrá privilegios de ver información",
        "US-39": "el CRM es el sistema de administracion es un panel dashboard para las computadoras",
        "US-40": "el PWA es una aplicacion mobile para las personas de campo",
    }
    with engine.begin() as connection:
        metadata.create_all(connection)
        for story_id, source in sources.items():
            connection.execute(history.insert().values(
                id=f"original-{story_id}", story_id=story_id, version=1, iteration="iteración 1",
                stakeholder="Dueño del producto", source_literal=source, source_type="Conversación",
                source_reference="source.md", normalized_story="Historia original", acceptance_criteria=[],
                unresolved_questions=[], linked_cards=[], recorded_by="stakeholder", created_at=None,
            ))
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        rows = connection.execute(select(history).order_by(history.c.version)).mappings().all()
        assert len(rows) == 6
        for story_id, source in sources.items():
            versions = [row for row in rows if row["story_id"] == story_id]
            assert [row["version"] for row in versions] == [1, 2]
            assert versions[0]["source_literal"] == versions[1]["source_literal"] == source
            assert versions[1]["unresolved_questions"]
        card_40 = next(row for row in rows if row["story_id"] == "US-40" and row["version"] == 2)
        assert "cola" in card_40["acceptance_criteria"][-1]
        assert "offline completo" in card_40["acceptance_criteria"][-1]

        migration.downgrade()
        remaining = connection.execute(select(history)).mappings().all()
        assert len(remaining) == 3
        assert {row["id"] for row in remaining} == {f"original-{story_id}" for story_id in sources}
