import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us37_live_menu_evidence_appends_without_changing_source_story() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic/versions/202611110128_us37_live_reference_menu.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    original = next(
        row for row in json.loads((root / "app/history_card_initial.json").read_text())
        if row["story_id"] == "US-37"
    )

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            **original,
            "id": str(uuid4()),
            "source_artifact": {"artifacts": [{"artifact_type": "WhatsApp", "reference": original["source_reference"]}]},
            "source_language": "es",
            "source_attribution": "Mario Groso",
            "source_confidence": "needs_validation",
            "source_links": [{"artifact_index": 0, "relation": "reconstruction", "location": ""}],
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-37").order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert versions[0]["source_literal"] == versions[1]["source_literal"] == original["source_literal"]
    evidence = versions[1]["source_artifact"]["artifacts"][-1]
    assert evidence["reference"] == migration.MENU_BUNDLE_URL
    assert evidence["sha256"] == migration.MENU_BUNDLE_SHA256
    assert versions[1]["source_links"][-1]["relation"] == "validation"
    assert [route for _, route in migration.MENU_ITEMS] == [
        "/", "/inventory", "/entries", "/exits", "/kardex", "/scanner",
        "/reports", "/suppliers", "/projects", "/users", "/settings",
    ]
    assert "vistas renderizadas" in versions[1]["unresolved_questions"][-1]
