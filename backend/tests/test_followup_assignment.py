from datetime import date, datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
import json
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

from app.models import Activity, Base, Customer, FollowUp, HistoryCard
from app.product_api import FollowUpDoneInput, FollowUpInput, _create_followup_record, auth_service, create_followup, list_followups, update_followup
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
        assert "push_claimed_at" not in row and "push_notified_at" not in row
        assert db.scalar(select(FollowUp).where(FollowUp.id == row["id"])).created_by == "admin@example.test"


def test_agent_followup_mutation_is_idempotent_by_confirmation_intent() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    users.create(engine)
    memberships.create(engine)
    admin = AuthIdentity("admin-id", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(users.insert(), {"id": "admin-id", "email": "admin@example.test", "name": "Admin", "password_hash": "x", "is_active": True, "created_at": now})
        connection.execute(memberships.insert(), {"user_id": "admin-id", "organization_id": "arcoenergy", "roles": ["administrador"], "permissions": list(ROLE_PERMISSIONS["administrador"]), "created_at": now})

    with Session(engine) as db, patch.object(auth_service, "engine", engine):
        customer = Customer(name="Cliente solar")
        db.add(customer); db.commit(); db.refresh(customer)
        data = FollowUpInput(customer_id=customer.id, due_date=date.today() + timedelta(days=3), note="Retomar propuesta")
        first = _create_followup_record(data, admin, db, agent_intent_id="intent-123")
        second = _create_followup_record(data, admin, db, agent_intent_id="intent-123")
        assert first.id == second.id
        assert db.scalar(select(sa.func.count()).select_from(FollowUp)) == 1
        assert db.scalar(select(sa.func.count()).select_from(Activity)) == 1

        with pytest.raises(HTTPException) as error:
            create_followup(
                FollowUpInput(customer_id=customer.id, due_date=date.today() + timedelta(days=3), assigned_to="disabled@example.test"),
                admin,
                db,
            )
        assert error.value.status_code == 422


def test_followups_are_scoped_to_responsible_user_and_admin() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    users.create(engine)
    memberships.create(engine)
    seller = AuthIdentity("seller-id", "arcoenergy", frozenset({"marketing"}), ROLE_PERMISSIONS["marketing"], "seller@example.test", "Vendedora")
    other = AuthIdentity("other-id", "arcoenergy", frozenset({"marketing"}), ROLE_PERMISSIONS["marketing"], "other@example.test", "Otro vendedor")
    admin = AuthIdentity("admin-id", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")

    with engine.begin() as connection:
        now = datetime.now(timezone.utc)
        connection.execute(users.insert(), [
            {"id": identity.user_id, "email": identity.email, "name": identity.name, "password_hash": "x", "is_active": True, "created_at": now}
            for identity in (seller, other, admin)
        ])
        connection.execute(memberships.insert(), [
            {"user_id": identity.user_id, "organization_id": "arcoenergy", "roles": list(identity.roles), "permissions": list(identity.permissions), "created_at": now}
            for identity in (seller, other, admin)
        ])

    with patch.object(auth_service, "engine", engine), Session(engine) as db:
        customer = Customer(name="Cliente solar")
        db.add(customer); db.flush()
        mine = FollowUp(customer_id=customer.id, due_date=date.today(), note="Mi llamada", assigned_to=seller.email)
        theirs = FollowUp(customer_id=customer.id, due_date=date.today(), note="Llamada ajena", assigned_to=other.email)
        db.add_all([mine, theirs]); db.commit()

        assert [row["id"] for row in list_followups(seller, db)] == [mine.id]
        assert {row["id"] for row in list_followups(admin, db)} == {mine.id, theirs.id}
        stale_admin_token = AuthIdentity(seller.user_id, seller.organization_id, admin.roles, admin.permissions, seller.email, seller.name)
        assert [row["id"] for row in list_followups(stale_admin_token, db)] == [mine.id]

        with pytest.raises(HTTPException) as error:
            update_followup(theirs.id, FollowUpDoneInput(done=True), seller, db)
        assert error.value.status_code == 403

        completed = update_followup(mine.id, FollowUpDoneInput(done=True), seller, db)
        assert completed["done"] is True

        reassignment = FollowUpInput(
            customer_id=customer.id, due_date=date.today() + timedelta(days=3),
            note="No puedo reasignar", assigned_to=other.email,
        )
        with pytest.raises(HTTPException) as error:
            create_followup(reassignment, seller, db)
        assert error.value.status_code == 403


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


def test_followup_access_migration_appends_versions_without_rewriting_literal_sources() -> None:
    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202611070055_followup_access_scope_card_revision.py"
    spec = spec_from_file_location(migration_path.stem, migration_path)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    records = json.loads((Path(__file__).parents[1] / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), records)
        originals = {
            row["story_id"]: row["source_literal"] for row in connection.execute(
                select(HistoryCard.story_id, HistoryCard.source_literal).where(HistoryCard.story_id.in_(["US-4", "US-14"]))
            ).mappings()
        }
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        revisions = connection.execute(select(HistoryCard.__table__).where(
            HistoryCard.story_id.in_(["US-4", "US-14"]), HistoryCard.iteration == migration.ITERATION,
        )).mappings().all()

    assert {row["story_id"] for row in revisions} == {"US-4", "US-14"}
    assert all(row["version"] == 2 and row["source_literal"] == originals[row["story_id"]] for row in revisions)

