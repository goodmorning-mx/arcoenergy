"""Run Alembic migrations under a PostgreSQL session advisory lock."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from app.database import create_database_engine

MIGRATION_LOCK_ID = 711_202_607_260_001
DEFAULT_LOCK_TIMEOUT_SECONDS = 120.0
DEFAULT_LOCK_POLL_SECONDS = 2.0


class MigrationLockTimeout(RuntimeError):
    """Raised when another release holds the schema migration lock too long."""


def lock_timeout_seconds() -> float:
    raw = os.getenv("MIGRATION_LOCK_TIMEOUT_SECONDS", str(DEFAULT_LOCK_TIMEOUT_SECONDS))
    value = float(raw)
    if value <= 0:
        raise ValueError("MIGRATION_LOCK_TIMEOUT_SECONDS must be greater than zero")
    return value


def acquire_migration_lock(
    connection: Connection,
    *,
    timeout_seconds: float,
    poll_seconds: float = DEFAULT_LOCK_POLL_SECONDS,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Acquire a session lock without waiting forever inside PostgreSQL."""

    deadline = clock() + timeout_seconds
    while True:
        acquired = bool(
            connection.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": MIGRATION_LOCK_ID},
            ).scalar_one()
        )
        connection.commit()
        if acquired:
            return
        if clock() >= deadline:
            raise MigrationLockTimeout(
                f"could not acquire migration lock within {timeout_seconds:g} seconds"
            )
        sleeper(min(poll_seconds, max(0.0, deadline - clock())))


def release_migration_lock(connection: Connection) -> None:
    released = bool(
        connection.execute(
            text("SELECT pg_advisory_unlock(:lock_id)"),
            {"lock_id": MIGRATION_LOCK_ID},
        ).scalar_one()
    )
    connection.commit()
    if not released:
        raise RuntimeError("migration advisory lock was not held by this session")


def alembic_config(connection: Connection) -> Config:
    backend_root = Path(__file__).resolve().parents[1]
    config = Config(str(backend_root / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


def run_migrations(
    engine: Engine | None = None,
    *,
    timeout_seconds: float | None = None,
) -> None:
    """Upgrade to Alembic head while holding one session-level lock."""

    database_engine = engine or create_database_engine()
    timeout = lock_timeout_seconds() if timeout_seconds is None else timeout_seconds
    if timeout <= 0:
        raise ValueError("migration lock timeout must be greater than zero")

    with database_engine.connect() as connection:
        locked = False
        migration_error: BaseException | None = None
        try:
            acquire_migration_lock(connection, timeout_seconds=timeout)
            locked = True
            command.upgrade(alembic_config(connection), "head")
        except BaseException as exc:
            migration_error = exc
            raise
        finally:
            if locked:
                try:
                    release_migration_lock(connection)
                except Exception:
                    if migration_error is None:
                        raise


def main() -> None:
    run_migrations()


if __name__ == "__main__":
    main()
