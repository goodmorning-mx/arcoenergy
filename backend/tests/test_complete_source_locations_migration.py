import hashlib
import importlib.util
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def _load_migration(root: Path):
    path = root / "alembic/versions/202611110130_complete_source_locations.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_remaining_cards_get_append_only_exact_source_locations() -> None:
    backend = Path(__file__).parents[1]
    migration = _load_migration(backend)
    initial = json.loads((backend / "app/history_card_initial.json").read_text())
    us21_path = backend / "alembic/versions/202611110102_us21_source_fidelity.py"
    us21_spec = importlib.util.spec_from_file_location(us21_path.stem, us21_path)
    assert us21_spec and us21_spec.loader
    us21_migration = importlib.util.module_from_spec(us21_spec)
    us21_spec.loader.exec_module(us21_migration)
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        for row in initial:
            connection.execute(HistoryCard.__table__.insert(), {
                **row,
                "id": str(uuid4()),
                "source_artifact": {"artifacts": [{"artifact_type": row["source_type"], "reference": row["source_reference"]}]},
                "source_language": "es",
                "source_attribution": row["stakeholder"],
                "source_confidence": "needs_validation",
                "source_links": [{"artifact_index": 0, "relation": "reconstruction", "location": ""}],
                "recorded_by": "source-import",
                "created_at": datetime.now(timezone.utc),
            })
        row = next(row for row in initial if row["story_id"] == "US-21")
        connection.execute(HistoryCard.__table__.insert(), {
            **row,
            "id": str(uuid4()),
            "version": 2,
            "iteration": "Iteración 90 · fidelidad de fuente US-21",
            "source_literal": us21_migration.SOURCE_LITERAL,
            "source_reference": "docs/discovery/sources/contador-comentarios-mejoras-original.docx",
            "source_artifact": {"artifacts": [{"artifact_type": "Documento Word", "reference": row["source_reference"]}]},
            "source_language": "es",
            "source_attribution": row["stakeholder"],
            "source_confidence": "verbatim",
            "source_links": [{"artifact_index": 0, "relation": "literal", "location": "ENTRADAS"}],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__).order_by(HistoryCard.story_id, HistoryCard.version)
        ).mappings().all()

    originals = {row["story_id"]: row for row in initial}
    for story_id in migration.CARD_LOCATORS:
        versions = [row for row in rows if row["story_id"] == story_id]
        expected_versions = [1, 2, 3] if story_id == "US-21" else [1, 2]
        assert [row["version"] for row in versions] == expected_versions
        assert versions[0]["source_literal"] == originals[story_id]["source_literal"]
        assert versions[-1]["source_literal"] == (us21_migration.SOURCE_LITERAL if story_id == "US-21" else originals[story_id]["source_literal"])
        assert versions[-1]["iteration"] == migration.ITERATION
        assert versions[-1]["source_confidence"] == "verbatim"
        assert versions[-1]["source_links"][-1]["location"] == migration.CARD_LOCATORS[story_id][1]

    assert set(migration.CARD_LOCATORS) | {"US-33", "US-34", "US-35"} == {f"US-{i}" for i in range(1, 43)}
    for story_id in ("US-33", "US-34", "US-35"):
        assert len([row for row in rows if row["story_id"] == story_id]) == 1


def test_source_manifest_hashes_match_checked_in_original_artifacts() -> None:
    repo = Path(__file__).parents[2]
    migration = _load_migration(Path(__file__).parents[1])
    for artifacts in migration.ARTIFACTS.values():
        for artifact in artifacts:
            path = repo / artifact["reference"]
            assert path.is_file()
            assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_story_source_literals_match_their_text_artifacts_or_explicit_composite_locators() -> None:
    backend = Path(__file__).parents[1]
    repo = backend.parent
    rows = json.loads((backend / "app/history_card_initial.json").read_text())

    def normalize(value: str) -> str:
        return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).casefold().replace(">", " ")).strip()

    for card in rows:
        story_id = card["story_id"]
        source_path = card["source_reference"].split(";", 1)[0]
        if card["source_type"] == "Documento Word/PDF":
            source_path = "docs/discovery/sources/contador-comentarios-mejoras-transcripcion.md"
        text = (repo / source_path).read_text()
        literal = card["source_literal"]
        if story_id == "US-21":
            # US-21's complete source is the append-only correction in revision 102.
            source_migration_path = backend / "alembic/versions/202611110102_us21_source_fidelity.py"
            spec = importlib.util.spec_from_file_location(source_migration_path.stem, source_migration_path)
            assert spec and spec.loader
            source_migration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(source_migration)
            source_text = (repo / "docs/discovery/sources/contador-comentarios-mejoras-transcripcion.md").read_text()
            assert normalize(source_migration.SOURCE_LITERAL) in normalize(source_text)
        elif story_id == "US-34":
            transcript = (repo / "docs/discovery/sources/contador-whatsapp-audio-transcripts-2026-11-02.md").read_text()
            timestamped_lines = [line for line in literal.splitlines() if line.strip().startswith("[") and "00:" in line]
            assert len(timestamped_lines) >= 10
            assert all(normalize(line.strip()) in normalize(transcript) for line in timestamped_lines)
        elif story_id == "US-35":
            source_text = (repo / "docs/discovery/sources/mario-groso-whatsapp-2026-11-05.md").read_text()
            message_blocks = [block.strip() for block in re.split(r"\n\s*\n", literal) if block.strip().startswith("[")]
            assert len(message_blocks) == 5
            assert all(normalize(block) in normalize(source_text) for block in message_blocks)
        else:
            assert normalize(literal) in normalize(text), story_id
