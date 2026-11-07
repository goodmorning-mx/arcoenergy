import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import MetaData, create_engine, inspect, select

from app.models import HistoryCard, Installation


def test_material_request_drive_migration_preserves_source_and_adds_access_revisions():
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070052_material_request_drive_and_access_audit.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    installation_columns = [column._copy() for column in Installation.__table__.columns
                            if not column.name.startswith("material_request_")]
    from sqlalchemy import Table
    Table("ae_installations", MetaData(), *installation_columns).create(engine)
    HistoryCard.__table__.create(engine)
    literals = {
        "US-25": "Subir una foto o PDF de la orden de trabajo para registrar salida de almacén y devoluciones.",
        "US-13": "Que todo se vaya a un drive para almacenar todos los datos",
        "US-14": "Si todo fuera desde una app, cada usuario tendrá privilegios de ver información",
        "US-39": "el CRM es el sistema de administracion es un panel dashboard para las computadoras y es el panel admin de todo.",
        "US-40": "el PWA es una aplicacion mobile para las personas de campo y ademas un cliente para los empleados.",
    }
    with engine.begin() as connection:
        for story_id, literal in literals.items():
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "source",
                "stakeholder": "stakeholder", "source_type": "WhatsApp", "source_reference": "source",
                "source_literal": literal, "normalized_story": "historia",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "source_artifact": {"artifacts": []}, "source_links": [], "source_language": "es",
                "source_attribution": "stakeholder", "source_confidence": "needs_validation",
                "recorded_by": "source-import", "created_at": datetime.now(timezone.utc),
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("ae_installations")}
        assert {"material_request_drive_file_id", "material_request_filename", "material_request_content_type", "material_request_updated_at"} <= columns
        for story_id, literal in literals.items():
            cards = connection.execute(select(HistoryCard.__table__).where(HistoryCard.story_id == story_id)
                                       .order_by(HistoryCard.version)).mappings().all()
            assert len(cards) == 2
            assert cards[0]["source_literal"] == cards[1]["source_literal"] == literal
            assert cards[1]["iteration"] == migration.ITERATION

