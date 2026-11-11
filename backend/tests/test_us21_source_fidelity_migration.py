import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard


def test_us21_appends_complete_word_source_without_rewriting_prior_version() -> None:
    base = Path(__file__).parents[1]
    migration_path = base / "alembic" / "versions" / "202611110102_us21_source_fidelity.py"
    spec = importlib.util.spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    initial = next(row for row in json.loads((base / "app" / "history_card_initial.json").read_text()) if row["story_id"] == "US-21")
    source_path = base.parent / "docs" / "discovery" / "sources" / "contador-comentarios-mejoras-original.docx"
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(source_path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    paragraphs = []
    for node in root.iter():
        if node.tag.endswith("}p"):
            text = "".join(child.text or "" for child in node.iter() if child.tag.endswith("}t"))
            if text.strip():
                paragraphs.append(text)
    start = paragraphs.index("ENTRADAS (DE INVETARIO)")
    section = []
    for paragraph in paragraphs[start:]:
        if section and paragraph.startswith("SALIDAS (DE INVENTARIO)"):
            break
        section.append(paragraph)
    assert migration.SOURCE_LITERAL == "\n\n".join(section)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), [{
            **initial,
            "id": str(uuid4()),
            "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        }])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-21").order_by(HistoryCard.version)
        ).mappings().all()
        assert len(versions) == 2
        assert versions[0]["source_literal"] == initial["source_literal"]
        assert versions[1]["version"] == 2
        assert versions[1]["source_literal"] == migration.SOURCE_LITERAL
        assert "fotografía de la factura" in versions[1]["source_literal"]
        assert "devolución de artículos" in versions[1]["source_literal"]
        assert versions[1]["recorded_by"] == "system:implementation-iteration"
