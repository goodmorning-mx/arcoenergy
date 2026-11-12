import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import drive_backup
from app.models import Base, BusinessSnapshotRun, HistoryCard


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, lambda: Session(engine)


def test_first_scheduled_snapshot_is_uploaded_and_durable_status_is_recorded(monkeypatch) -> None:
    engine, sessions = _database()
    monkeypatch.setattr(drive_backup, "get_settings", lambda: type("Settings", (), {
        "google_drive_folder_id": "private-folder",
        "google_drive_service_account_json": "configured",
        "business_snapshot_interval_hours": 24,
    })())
    archive = Mock(return_value={"filename": "arcoenergy-datos-daily.json", "bytes": 1200, "record_count": 35})
    now = datetime.now(timezone.utc)

    result = drive_backup.run_scheduled_business_snapshot(session_factory=sessions, archive_fn=archive, now=now)

    assert result["status"] == "succeeded"
    assert result["filename"] == "arcoenergy-datos-daily.json"
    archive.assert_called_once()
    with Session(engine) as db:
        row = db.scalar(select(BusinessSnapshotRun))
        assert row.status == "succeeded"
        assert row.completed_at is not None
        assert row.file_bytes == 1200
        assert row.record_count == 35


def test_scheduled_snapshot_waits_until_interval_elapses(monkeypatch) -> None:
    engine, sessions = _database()
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        db.add(BusinessSnapshotRun(status="succeeded", started_at=now - timedelta(hours=1), completed_at=now - timedelta(hours=1), filename="last.json"))
        db.commit()
    monkeypatch.setattr(drive_backup, "get_settings", lambda: type("Settings", (), {
        "google_drive_folder_id": "private-folder",
        "google_drive_service_account_json": "configured",
        "business_snapshot_interval_hours": 24,
    })())
    archive = Mock()

    result = drive_backup.run_scheduled_business_snapshot(session_factory=sessions, archive_fn=archive, now=now)

    assert result["status"] == "not_due"
    archive.assert_not_called()


def test_scheduled_snapshot_stays_idle_until_private_drive_is_configured(monkeypatch) -> None:
    engine, sessions = _database()
    monkeypatch.setattr(drive_backup, "get_settings", lambda: type("Settings", (), {
        "google_drive_folder_id": "",
        "google_drive_service_account_json": "",
        "business_snapshot_interval_hours": 24,
    })())
    archive = Mock()

    result = drive_backup.run_scheduled_business_snapshot(session_factory=sessions, archive_fn=archive)

    assert result["status"] == "waiting_for_drive_configuration"
    archive.assert_not_called()
    with Session(engine) as db:
        assert db.scalar(select(BusinessSnapshotRun.id)) is None


def test_failed_drive_upload_records_safe_error_and_retries_later(monkeypatch) -> None:
    engine, sessions = _database()
    monkeypatch.setattr(drive_backup, "get_settings", lambda: type("Settings", (), {
        "google_drive_folder_id": "private-folder",
        "google_drive_service_account_json": "configured",
        "business_snapshot_interval_hours": 24,
    })())
    now = datetime.now(timezone.utc)
    result = drive_backup.run_scheduled_business_snapshot(
        session_factory=sessions, archive_fn=Mock(side_effect=RuntimeError("private OAuth detail")), now=now,
    )

    assert result == {"status": "failed", "error_code": "private_drive_upload_failed"}
    with Session(engine) as db:
        row = db.scalar(select(BusinessSnapshotRun))
        assert row.status == "failed"
        assert row.error_code == "private_drive_upload_failed"
        assert "OAuth" not in row.error_code


def test_us13_scheduled_snapshot_migration_adds_table_and_appends_story() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611110136_us13_scheduled_private_drive_snapshots.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    source = next(row for row in records if row["story_id"] == "US-13")
    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), {
            **source, "id": str(uuid4()), "recorded_by": "source-import",
            "created_at": datetime.now(timezone.utc),
        })
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        rows = connection.execute(
            select(HistoryCard.__table__)
            .where(HistoryCard.story_id == "US-13")
            .order_by(HistoryCard.version)
        ).mappings().all()

    assert len(rows) == 2
    assert rows[0]["source_literal"] == rows[1]["source_literal"] == source["source_literal"]
    assert rows[-1]["iteration"] == migration.ITERATION
    assert any("cada intervalo configurado" in item for item in rows[-1]["acceptance_criteria"])
