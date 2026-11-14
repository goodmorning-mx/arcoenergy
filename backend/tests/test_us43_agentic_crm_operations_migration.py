import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_agentic_crm_requirement_is_appended_without_rewriting_original_cards() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611130148_us43_agentic_crm_operations.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    engine = create_engine("sqlite://")
    table = HistoryCard.__table__

    with engine.begin() as connection:
        table.create(connection)
        now = datetime.now(timezone.utc)
        for source in records:
            connection.execute(table.insert(), {
                **source, "id": str(uuid4()), "recorded_by": "source-import", "created_at": now,
            })
        original_us42 = connection.execute(select(table).where(table.c.story_id == "US-42")).mappings().one()
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        rows = connection.execute(select(table).order_by(table.c.story_id, table.c.version)).mappings().all()
        cards = {row["story_id"] for row in rows}
        us43 = [row for row in rows if row["story_id"] == "US-43"]
        us42 = [row for row in rows if row["story_id"] == "US-42"]

    assert len(cards) == 43
    assert len(us43) == 1 and us43[0]["version"] == 1
    assert us43[0]["source_literal"] == migration.SOURCE_LITERAL
    assert us43[0]["source_reference"] == "docs/discovery/sources/owner-agentic-crm-requirement.md"
    assert us43[0]["source_confidence"] == "literal_user_message"
    assert us43[0]["source_literal"] != ""
    source_doc = (root.parent / "docs" / "discovery" / "sources" / "owner-agentic-crm-requirement.md").read_text(encoding="utf-8")
    assert f"> {migration.SOURCE_LITERAL}" in source_doc
    assert us42[0]["source_literal"] == original_us42["source_literal"]
    assert us42[-1]["version"] == original_us42["version"] + 1
    assert migration.US42_AUDIT[0] in us42[-1]["acceptance_criteria"]
    assert migration.US42_AUDIT[1] in us42[-1]["unresolved_questions"]
