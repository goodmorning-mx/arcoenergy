import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_live_anonymous_audit_appends_to_us14_without_changing_source() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic/versions/202611110129_us14_live_anonymous_read_audit.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    original = next(
        row for row in json.loads((root / "app/history_card_initial.json").read_text())
        if row["story_id"] == "US-14"
    )
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            **original,
            "id": str(uuid4()),
            "source_artifact": {"artifacts": [{"artifact_type": "WhatsApp", "reference": original["source_reference"]}]},
            "source_language": "es",
            "source_attribution": "Goito Profugo",
            "source_confidence": "needs_validation",
            "source_links": [{"artifact_index": 0, "relation": "reconstruction", "location": ""}],
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-14").order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == original["source_literal"]
    assert versions[1]["source_artifact"]["artifacts"][-1]["sha256"] == migration.OPENAPI_SHA256
    assert versions[1]["source_links"][-1]["relation"] == "validation"
    assert "34/34" in versions[1]["source_links"][-1]["location"]
    assert "HTTP 401" in versions[1]["acceptance_criteria"][-1]
    assert "o campo" in versions[1]["unresolved_questions"][-1]
