from datetime import date, datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
from gm_auth.models import AuthIdentity, memberships, users
import pytest
from sqlalchemy import Boolean, Column, Date, DateTime, MetaData, String, Text, create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, Customer, FollowUp, HistoryCard
from app.product_api import FollowUpInput, auth_service, create_followup
from app.roles import ROLE_PERMISSIONS


def test_followup_is_assigned_to_active_commercial_member_and_records_owner() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    users.create(engine)
    memberships.create(engine)
    admin = AuthIdentity("admin-id", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with engine.begin() as connection:
        timestamp = datetime.now(timezone.utc)
        connection.execute(users.insert(), [
            {"id": "admin-id", "email": "admin@example.test", "name": "Admin", "password_hash": "x", "is_active": True, "created_at": timestamp},
            {"id": "seller-id", "email": "seller@example.test", "name": "Vendedora", "password_hash": "x", "is_active": True, "created_at": timestamp},
            {"id": "disabled-id", "email": "disabled@example.test", "name": "Baja", "password_hash": "x", "is_active": False, "created_at": timestamp},
        ])
        connection.execute(memberships.insert(), [
            {"user_id": "admin-id", "organization_id": "arcoenergy", "roles": ["administrador"], "permissions": list(ROLE_PERMISSIONS["administrador"]), "created_at": timestamp},
            {"user_id": "seller-id", "organization_id": "arcoenergy", "roles": ["marketing"], "permissions": list(ROLE_PERMISSIONS["marketing"]), "created_at": timestamp},
            {"user_id": "disabled-id", "organization_id": "arcoenergy", "roles": ["marketing"], "permissions": list(ROLE_PERMISSIONS["marketing"]), "created_at": timestamp},
        ])

    with Session(engine) as db, patch.object(auth_service, "engine", engine):
        customer = Customer(name="Cliente solar")
        db.add(customer); db.commit(); db.refresh(customer)
        row = create_followup(
            FollowUpInput(customer_id=customer.id, due_date=date.today() + timedelta(days=3), note="Retomar propuesta", assigned_to="SELLER@example.test"),
            admin,
            db,
        )
        assert row["assigned_to"] == "seller@example.test"
        assert db.scalar(select(FollowUp).where(FollowUp.id == row["id"])).created_by == "admin@example.test"

        with pytest.raises(HTTPException) as error:
            create_followup(
                FollowUpInput(customer_id=customer.id, due_date=date.today() + timedelta(days=3), assigned_to="disabled@example.test"),
                admin,
                db,
            )
        assert error.value.status_code == 422


def test_followup_assignment_migration_backfills_creator_and_appends_us4_revision() -> None:
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202611060040_followup_responsibility_card_revision.py"
    spec = spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    legacy_followups = sa.Table(
        "ae_followups", MetaData(),
        Column("id", String(36), primary_key=True), Column("customer_id", String(36), nullable=False),
        Column("quote_id", String(36)), Column("due_date", Date, nullable=False), Column("note", Text, nullable=False),
        Column("created_by", String(180), nullable=False), Column("done", Boolean, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )
    legacy_followups.create(engine)
    HistoryCard.__table__.create(engine)
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(legacy_followups.insert(), {"id": "followup-1", "customer_id": "customer-1", "due_date": date.today(), "note": "Llamar", "created_by": "owner@example.test", "done": False, "created_at": now})
        connection.execute(HistoryCard.__table__.insert(), {
            "id": str(uuid4()), "story_id": "US-4", "version": 1, "iteration": "initial",
            "stakeholder": "Goito", "source_type": "WhatsApp", "source_reference": "source",
            "source_literal": "Fuente US-4", "normalized_story": "Programar seguimientos",
            "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [],
            "recorded_by": "source-import", "created_at": now,
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        migrated_followups = sa.Table("ae_followups", MetaData(), autoload_with=connection)
        followup = connection.execute(sa.select(migrated_followups)).mappings().one()
        history = connection.execute(sa.select(HistoryCard.__table__).where(HistoryCard.story_id == "US-4", HistoryCard.version == 2)).mappings().one()

    assert followup["assigned_to"] == "owner@example.test"
    assert "responsable miembro activo" in " ".join(history["acceptance_criteria"])

