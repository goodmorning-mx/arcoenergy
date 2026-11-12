"""Periodic, private business snapshots in the configured Google Drive folder."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.config import get_settings
from app.models import BusinessSnapshotRun

logger = logging.getLogger(__name__)
_ADVISORY_LOCK_KEY = 731940135
_ACTIVE_RUN_LEASE = timedelta(hours=2)
_POLL_SECONDS = 300


def run_scheduled_business_snapshot(*, session_factory=None, archive_fn=None, now: datetime | None = None) -> dict:
    """Create one snapshot when due; a durable lease prevents duplicate replicas."""
    settings = get_settings()
    if not settings.google_drive_folder_id or not settings.google_drive_service_account_json:
        return {"status": "waiting_for_drive_configuration"}

    if session_factory is None or archive_fn is None:
        from app.product_api import SessionLocal
        from app.drive_archive import archive_business_snapshot

        session_factory = session_factory or SessionLocal
        archive_fn = archive_fn or archive_business_snapshot

    timestamp = now or datetime.now(timezone.utc)
    interval = timedelta(hours=settings.business_snapshot_interval_hours)

    with session_factory() as db:
        if db.get_bind().dialect.name == "postgresql":
            lock_acquired = db.scalar(
                text("SELECT pg_try_advisory_xact_lock(:lock_key)"),
                {"lock_key": _ADVISORY_LOCK_KEY},
            )
            if not lock_acquired:
                db.rollback()
                return {"status": "another_instance_running"}

        recent_active = db.scalar(
            select(BusinessSnapshotRun)
            .where(
                BusinessSnapshotRun.status == "running",
                BusinessSnapshotRun.started_at >= timestamp - _ACTIVE_RUN_LEASE,
            )
            .order_by(BusinessSnapshotRun.started_at.desc())
            .limit(1)
        )
        if recent_active:
            db.rollback()
            return {"status": "snapshot_in_progress"}

        last_success = db.scalar(
            select(BusinessSnapshotRun.completed_at)
            .where(BusinessSnapshotRun.status == "succeeded")
            .order_by(BusinessSnapshotRun.completed_at.desc())
            .limit(1)
        )
        if last_success:
            if last_success.tzinfo is None:
                last_success = last_success.replace(tzinfo=timezone.utc)
            if timestamp - last_success < interval:
                db.rollback()
                return {"status": "not_due", "last_success_at": last_success.isoformat()}

        stale_runs = db.scalars(select(BusinessSnapshotRun).where(
            BusinessSnapshotRun.status == "running",
            BusinessSnapshotRun.started_at < timestamp - _ACTIVE_RUN_LEASE,
        )).all()
        for stale in stale_runs:
            stale.status = "failed"
            stale.completed_at = timestamp
            stale.error_code = "worker_lease_expired"

        run = BusinessSnapshotRun(status="running", started_at=timestamp)
        db.add(run)
        db.commit()
        run_id = run.id

    try:
        with session_factory() as db:
            result = archive_fn(db)
    except Exception:
        logger.warning("Scheduled private business snapshot failed.")
        with session_factory() as db:
            run = db.get(BusinessSnapshotRun, run_id)
            if run:
                run.status = "failed"
                run.completed_at = datetime.now(timezone.utc)
                run.error_code = "private_drive_upload_failed"
                db.commit()
        return {"status": "failed", "error_code": "private_drive_upload_failed"}

    completed_at = datetime.now(timezone.utc)
    with session_factory() as db:
        run = db.get(BusinessSnapshotRun, run_id)
        if run:
            run.status = "succeeded"
            run.completed_at = completed_at
            run.filename = str(result.get("filename", ""))[:255]
            run.file_bytes = int(result.get("bytes", 0))
            run.record_count = int(result.get("record_count", 0))
            run.error_code = ""
            db.commit()

    return {
        "status": "succeeded",
        "filename": str(result.get("filename", "")),
        "bytes": int(result.get("bytes", 0)),
        "record_count": int(result.get("record_count", 0)),
        "completed_at": completed_at.isoformat(),
    }


async def business_snapshot_loop() -> None:
    """Poll every five minutes; persist schedule state so restarts do not duplicate runs."""
    while True:
        try:
            await asyncio.to_thread(run_scheduled_business_snapshot)
        except Exception:
            logger.warning("Scheduled private business snapshot cycle failed.")
        await asyncio.sleep(_POLL_SECONDS)
