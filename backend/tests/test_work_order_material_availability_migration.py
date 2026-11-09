import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_order_availability_iteration_appends_history_without_replacing_source():
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611090077_work_order_material_availability.py"
    spec = importlib.util.spec_from_file_location("work_order_material_availability", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__
    source_literal = "ellos pueden revisar el stock desde la app para ver si todo está disponible"
    with engine.begin() as connection:
        table.create(connection)
        connection.execute(table.insert().values(
            id="source-us-8", story_id="US-8", version=1,
            iteration="discovery inicial", stakeholder="Goito Profugo",
            source_literal=source_literal, source_type="WhatsApp", source_reference="conversation",
            normalized_story="Consultar stock por instalación", acceptance_criteria=[],
            unresolved_questions=[], linked_cards=[], recorded_by="stakeholder",
            created_at=datetime.now(timezone.utc),
        ))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(table).order_by(table.c.version)).mappings().all()
        assert [row["version"] for row in rows] == [1, 2]
        assert rows[0]["source_literal"] == rows[1]["source_literal"] == source_literal
        assert all(any(text in criterion for criterion in rows[1]["acceptance_criteria"])
                   for text in ("Cada orden muestra", "no repiten un déficit global"))
