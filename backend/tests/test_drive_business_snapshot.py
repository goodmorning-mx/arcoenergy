import json
import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select
from fastapi import HTTPException
from gm_auth.models import AuthIdentity

from app.drive_archive import EXCLUDED_TABLES, build_business_snapshot
from app.models import Base, Customer, HistoryCard, OfflineOperation, PushSubscription
from app.roles import ROLE_PERMISSIONS
from app import product_api

ROOT = Path(__file__).resolve().parents[1]


def test_business_snapshot_includes_domain_and_roles_but_excludes_device_secrets() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Customer(name="Cliente de prueba", phone="5551234567", email="cliente@example.test", city="Tampico"))
        db.add(PushSubscription(user_email="field@example.test", endpoint="https://push.example.test/private", p256dh="private-key", auth="private-auth"))
        db.add(OfflineOperation(owner_email="field@example.test", operation_id="operation-1", operation_type="expense", payload_hash="a" * 64))
        db.flush()
        content, count, filename = build_business_snapshot(db, team_members_override=[{
            "id": "team-1", "email": "admin@example.test", "name": "Admin", "is_active": True,
            "roles": ["administrador"], "permissions": ["team:manage"],
        }])

    snapshot = json.loads(content)
    assert filename.startswith("arcoenergy-datos-") and filename.endswith(".json")
    assert snapshot["format"] == "arcoenergy-business-data-v1"
    assert snapshot["record_count"] == count == 2
    assert snapshot["tables"]["ae_customers"][0]["name"] == "Cliente de prueba"
    assert "ae_history_cards" in snapshot["tables"]
    assert "ae_push_subscriptions" not in snapshot["tables"]
    assert "ae_offline_operations" not in snapshot["tables"]
    assert "ae_integrations" not in snapshot["tables"]
    assert snapshot["excluded_tables"] == EXCLUDED_TABLES
    assert snapshot["team_members"][0]["roles"] == ["administrador"]
    assert b"private-key" not in content and b"private-auth" not in content
    assert b"operation-1" not in content


def test_drive_export_reports_unconfigured_folder_without_claiming_success(monkeypatch) -> None:
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    monkeypatch.setattr(product_api, "folder_status", lambda _settings: {"connected": False, "status": "credentials_not_configured"})
    monkeypatch.setattr(product_api, "archive_business_snapshot", lambda _db: (_ for _ in ()).throw(AssertionError("must not upload")))

    with create_engine("sqlite://").connect() as connection:
        with Session(bind=connection) as db:
            try:
                product_api.export_business_snapshot(identity, db)
            except HTTPException as error:
                assert error.status_code == 503
                assert "no está conectado" in error.detail
            else:
                raise AssertionError("unconfigured Drive must not return success")


def test_drive_export_returns_only_safe_file_metadata_after_private_save(monkeypatch) -> None:
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    monkeypatch.setattr(product_api, "folder_status", lambda _settings: {"connected": True, "status": "connected"})
    monkeypatch.setattr(product_api, "archive_business_snapshot", lambda _db: {
        "filename": "arcoenergy-datos-20261112T000000Z.json", "file_id": "private-drive-id", "bytes": 4321, "record_count": 42,
    })

    with create_engine("sqlite://").connect() as connection:
        with Session(bind=connection) as db:
            result = product_api.export_business_snapshot(identity, db)

    assert result == {
        "saved": True, "filename": "arcoenergy-datos-20261112T000000Z.json",
        "bytes": 4321, "record_count": 42, "storage": "private_google_drive",
    }
    assert "file_id" not in result


def test_drive_export_rejects_non_administrator_even_with_team_permission(monkeypatch) -> None:
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"] | {"team:manage"}, "accountant@example.test", "Contador")
    monkeypatch.setattr(product_api, "folder_status", lambda _settings: (_ for _ in ()).throw(AssertionError("must reject before Drive")))
    with create_engine("sqlite://").connect() as connection:
        with Session(bind=connection) as db:
            try:
                product_api.export_business_snapshot(identity, db)
            except HTTPException as error:
                assert error.status_code == 403
            else:
                raise AssertionError("non-administrator export must be denied")


def test_drive_snapshot_iteration_appends_us13_without_rewriting_source() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    rows = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for row in rows:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    path = ROOT / "alembic" / "versions" / "202611110132_us13_private_drive_business_snapshot.py"
    spec = importlib.util.spec_from_file_location(path.name, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), rows)
        source = connection.scalar(select(HistoryCard.source_literal).where(
            HistoryCard.story_id == "US-13", HistoryCard.version == 1,
        ))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(select(
            HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal,
            HistoryCard.acceptance_criteria, HistoryCard.unresolved_questions,
        ).where(HistoryCard.story_id == "US-13").order_by(HistoryCard.version)).all()

    assert len(versions) == 2
    assert all(row.source_literal == source for row in versions)
    assert versions[1].iteration == "Iteración 120 · exportación privada de datos a Drive · 2026-11-11"
    assert any("exportación JSON privada" in item for item in versions[1].acceptance_criteria)
    assert any("restauración" in item for item in versions[1].unresolved_questions)
