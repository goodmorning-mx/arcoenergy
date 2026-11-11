import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from app.models import HistoryCard


def test_installer_push_migration_accepts_current_user_email_schema() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611080073_installer_push_subscriptions.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_push_subscriptions (id VARCHAR(36) PRIMARY KEY, user_email VARCHAR(180) NOT NULL, endpoint TEXT NOT NULL, p256dh VARCHAR(200) NOT NULL, auth VARCHAR(100) NOT NULL, created_at DATETIME NOT NULL)"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        indexes = {index["name"] for index in inspect(connection).get_indexes("ae_push_subscriptions")}
        assert "ix_ae_push_subscriptions_user_email" in indexes
