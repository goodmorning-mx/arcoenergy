import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from gm_auth.models import memberships

from app.models import Base


ROOT = Path(__file__).resolve().parents[1]


def test_report_permission_is_granted_to_existing_accounting_roles_only() -> None:
    spec = importlib.util.spec_from_file_location(
        "profitability_report_permissions",
        ROOT / "alembic" / "versions" / "202611060018_profitability_report_permissions.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    memberships.metadata.create_all(engine)
    with engine.begin() as connection:
        now = datetime.now(timezone.utc)
        connection.execute(memberships.insert(), [
            {"user_id": "u-admin", "organization_id": "arcoenergy", "roles": ["administrador"], "permissions": ["sales:read"], "created_at": now},
            {"user_id": "u-accountant", "organization_id": "arcoenergy", "roles": ["contador"], "permissions": [], "created_at": now},
            {"user_id": "u-marketing", "organization_id": "arcoenergy", "roles": ["marketing"], "permissions": ["customers:read"], "created_at": now},
        ])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

    with Session(engine) as db:
        permissions = {row.user_id: set(row.permissions) for row in db.execute(select(memberships.c.user_id, memberships.c.permissions)).all()}
    assert "reports:read" in permissions["u-admin"]
    assert "reports:read" in permissions["u-accountant"]
    assert "reports:read" not in permissions["u-marketing"]
