import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import Customer, HistoryCard, Installation, Project


def test_migration_backfills_existing_lead_and_revises_story_cards() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611060038_installation_crew_assignments.py"
    spec = importlib.util.spec_from_file_location(path.name, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    Customer.__table__.create(engine)
    Project.__table__.create(engine)
    Installation.__table__.create(engine)
    HistoryCard.__table__.create(engine)
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(Customer.__table__.insert(), {"id": "customer-1", "name": "Cliente", "phone": "", "email": "", "city": "", "address": "", "status": "lead", "source": "", "created_at": now})
        connection.execute(Installation.__table__.insert(), [
            {"id": "legacy-order", "customer_id": "customer-1", "lead_installer": " Crew@Example.Test ", "status": "scheduled", "checklist": [], "notes": ""},
            {"id": "unassigned-order", "customer_id": "customer-1", "lead_installer": "", "status": "scheduled", "checklist": [], "notes": ""},
        ])
        for story_id in ("US-7", "US-40"):
            connection.execute(HistoryCard.__table__.insert(), {
                "id": str(uuid4()), "story_id": story_id, "version": 1, "iteration": "initial",
                "stakeholder": "Equipo", "source_type": "conversation", "source_reference": "history",
                "source_literal": f"Fuente {story_id}", "normalized_story": "Historia",
                "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
                "recorded_by": "source-import", "created_at": now,
            })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        assignments_table = sa.Table("ae_installation_assignments", sa.MetaData(), autoload_with=connection)
        assignments = connection.execute(select(assignments_table.c.installation_id, assignments_table.c.installer_email)).all()
        versions = connection.execute(select(HistoryCard.story_id, HistoryCard.version)
            .where(HistoryCard.story_id.in_(["US-7", "US-40"]), HistoryCard.version == 2)).all()

    assert [(row.installation_id, row.installer_email) for row in assignments] == [("legacy-order", "crew@example.test")]
    assert {(row.story_id, row.version) for row in versions} == {("US-7", 2), ("US-40", 2)}
