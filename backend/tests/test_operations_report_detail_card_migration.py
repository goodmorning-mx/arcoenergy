import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_operations_report_details_revision_preserves_source_card():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080068_operations_report_detail_card.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    literal = "El contador pidió ver operaciones relacionadas."
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-29", "version": 2,
            "iteration": "source", "stakeholder": "Contador",
            "source_literal": literal, "source_type": "WhatsApp",
            "source_reference": "source", "normalized_story": "Reporte operativo",
            "acceptance_criteria": ["Original"], "unresolved_questions": [], "linked_cards": [],
            "source_artifact": {"artifacts": []}, "source_language": "es",
            "source_attribution": "Contador", "source_confidence": "needs_validation",
            "source_links": [], "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == "US-29").order_by(HistoryCard.version)).mappings().all()

    assert [row["version"] for row in rows] == [2, 3]
    assert [row["source_literal"] for row in rows] == [literal, literal]
    assert "Original" in rows[1]["acceptance_criteria"]
    assert any("lista clientes por estado" in item for item in rows[1]["acceptance_criteria"])
    assert rows[1]["iteration"] == migration.ITERATION
