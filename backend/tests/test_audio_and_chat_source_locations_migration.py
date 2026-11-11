import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_source_location_migration_appends_versions_and_keeps_original_literals() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611110127_audio_and_chat_source_locations.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    originals = {
        row["story_id"]: row
        for row in json.loads((root / "app" / "history_card_initial.json").read_text())
        if row["story_id"] in {"US-33", "US-34", "US-35"}
    }
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        for row in originals.values():
            connection.execute(HistoryCard.__table__.insert(), {
                **row, "id": str(uuid4()), "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.story_id.in_(list(originals)))
            .order_by(HistoryCard.story_id, HistoryCard.version)
        ).mappings().all()

    for story_id, original in originals.items():
        versions = [row for row in rows if row["story_id"] == story_id]
        assert [row["version"] for row in versions] == [1, 2]
        assert versions[0]["source_literal"] == original["source_literal"]
        assert versions[1]["source_literal"] == original["source_literal"]
        assert versions[1]["iteration"] == migration.ITERATION
        assert versions[1]["source_links"]
    us33, us34, us35 = [row for row in rows if row["version"] == 2]
    assert us33["source_confidence"] == "transcription"
    assert us33["source_artifact"]["artifacts"][0]["sha256"] == "e2582c5049ad54cfe0d7b48308661c1afa0f75899f2ba7de807c380f49707c04"
    assert len(us34["source_artifact"]["artifacts"]) == 3
    assert us34["source_links"][0]["location"].endswith("00:00–00:23")
    assert us34["source_links"][1]["location"].endswith("00:00–00:38")
    assert us35["source_confidence"] == "verbatim"
    assert len(us35["source_links"]) == 5
    assert us35["source_attribution"] == "Mario Groso"


def test_audio_source_hashes_match_the_source_manifest() -> None:
    root = Path(__file__).parents[2]
    manifest = (root / "docs/discovery/sources/contador-whatsapp-audio-transcripts-2026-11-02.md").read_text()
    path = Path(__file__).parents[1] / "alembic/versions/202611110127_audio_and_chat_source_locations.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    for payload in migration.AUDIO_CARDS.values():
        for artifact in payload["source_artifact"]["artifacts"]:
            if artifact["sha256"]:
                assert artifact["sha256"] in manifest
