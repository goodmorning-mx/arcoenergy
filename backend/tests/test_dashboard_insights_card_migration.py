import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_dashboard_iteration_appends_us37_without_changing_source_literal() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611100082_dashboard_insights_card.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    source_literal = "El DASHBOARD está bien, aquí debemos de poder ver detalles importantes."
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-37", "version": 4, "iteration": "previous",
            "stakeholder": "Mario Groso", "source_type": "Word", "source_reference": "contador-original.docx",
            "source_literal": source_literal, "normalized_story": "Revisar dashboard",
            "acceptance_criteria": ["Los indicadores deben reflejar los registros."],
            "unresolved_questions": [], "linked_cards": ["US-38"],
            "recorded_by": "source-import", "created_at": now,
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-37").order_by(HistoryCard.version)
        ).mappings().all()

    assert [row["version"] for row in versions] == [4, 5]
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == source_literal
    assert versions[1]["linked_cards"] == ["US-38"]
    assert any("siete días" in item for item in versions[1]["acceptance_criteria"])
