from __future__ import annotations

from unittest.mock import patch

import pytest

from app import migrations


class FakeResult:
    def __init__(self, value: bool):
        self.value = value

    def scalar_one(self) -> bool:
        return self.value


class FakeConnection:
    def __init__(self, results: list[bool]):
        self.results = iter(results)
        self.statements: list[str] = []
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, statement, parameters):
        self.statements.append(str(statement))
        assert parameters == {"lock_id": migrations.MIGRATION_LOCK_ID}
        return FakeResult(next(self.results))

    def commit(self):
        self.commits += 1


class FakeEngine:
    def __init__(self, connection: FakeConnection):
        self.connection = connection

    def connect(self):
        return self.connection


def test_run_migrations_holds_one_connection_lock() -> None:
    connection = FakeConnection([True, True])
    engine = FakeEngine(connection)

    with patch.object(migrations.command, "upgrade") as upgrade:
        migrations.run_migrations(engine, timeout_seconds=1)

    assert "pg_try_advisory_lock" in connection.statements[0]
    assert "pg_advisory_unlock" in connection.statements[1]
    assert connection.commits == 2
    config, revision = upgrade.call_args.args
    assert revision == "head"
    assert config.attributes["connection"] is connection


def test_failed_migration_releases_lock_and_stops_startup() -> None:
    connection = FakeConnection([True, True])
    engine = FakeEngine(connection)

    with patch.object(migrations.command, "upgrade", side_effect=RuntimeError("bad revision")):
        with pytest.raises(RuntimeError, match="bad revision"):
            migrations.run_migrations(engine, timeout_seconds=1)

    assert "pg_advisory_unlock" in connection.statements[-1]


def test_lock_timeout_fails_closed() -> None:
    connection = FakeConnection([False])
    clocks = iter([0.0, 1.0])

    with pytest.raises(migrations.MigrationLockTimeout):
        migrations.acquire_migration_lock(
            connection,
            timeout_seconds=0.5,
            sleeper=lambda _seconds: None,
            clock=lambda: next(clocks),
        )

    assert connection.commits == 1
    assert all("pg_advisory_unlock" not in statement for statement in connection.statements)
