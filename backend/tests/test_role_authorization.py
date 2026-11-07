from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine

from app.product_api import require_permissions
from gm_auth.models import AuthIdentity, metadata, memberships, organizations, users


def _service_with_membership(*, role: str, permissions: set[str], active: bool = True):
    engine = create_engine("sqlite://")
    metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with engine.begin() as connection:
        connection.execute(organizations.insert(), {"id": "arcoenergy", "slug": "arcoenergy", "name": "ArcoEnergy", "created_at": now})
        connection.execute(users.insert(), {"id": "user-1", "email": "staff@example.test", "name": "Equipo", "password_hash": "unused", "is_active": active, "created_at": now})
        connection.execute(memberships.insert(), {"user_id": "user-1", "organization_id": "arcoenergy", "roles": [role], "permissions": sorted(permissions), "created_at": now})
    return SimpleNamespace(engine=engine), AuthIdentity("user-1", "arcoenergy", frozenset({role}), frozenset(permissions), "staff@example.test", "Equipo")


def test_permission_dependency_allows_current_membership_grant() -> None:
    service, identity = _service_with_membership(role="marketing", permissions={"customers:read", "customers:write"})
    dependency = require_permissions(service, "customers:write")

    assert dependency(identity) == identity


def test_permission_dependency_rejects_stale_token_grant_after_role_change() -> None:
    service, stale_admin_identity = _service_with_membership(role="instalador", permissions={"inventory:read", "inventory:write"})
    stale_admin_identity = AuthIdentity(
        stale_admin_identity.user_id, stale_admin_identity.organization_id,
        frozenset({"administrador"}), frozenset({"inventory:manage", "team:manage"}),
        stale_admin_identity.email, stale_admin_identity.name,
    )

    with pytest.raises(HTTPException) as result:
        require_permissions(service, "team:manage")(stale_admin_identity)

    assert result.value.status_code == 403


def test_permission_dependency_rejects_inactive_member() -> None:
    service, identity = _service_with_membership(role="administrador", permissions={"team:manage"}, active=False)

    with pytest.raises(HTTPException) as result:
        require_permissions(service, "team:manage")(identity)

    assert result.value.status_code == 401
