from types import SimpleNamespace
from unittest.mock import Mock

from app import auth
from app.roles import ROLE_PERMISSIONS


class _Result:
    def first(self):
        return ("existing-bootstrap-user",)


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _statement):
        return _Result()


class _Engine:
    def connect(self):
        return _Connection()


def test_refresh_session_lifetime_has_no_operational_idle_timeout() -> None:
    assert auth.settings.auth_refresh_days == 36_500
    assert auth.auth_service.settings.refresh_days == 36_500


def test_bootstrap_admin_refreshes_existing_configured_account_role_and_permissions(monkeypatch) -> None:
    set_membership = Mock()
    create_user = Mock()
    monkeypatch.setattr(auth, "settings", SimpleNamespace(
        admin_bootstrap_email="owner@example.test",
        admin_bootstrap_password="a-long-runtime-secret",
        organization_id="arcoenergy",
    ))
    monkeypatch.setattr(auth, "auth_engine", _Engine())
    monkeypatch.setattr(auth.auth_service, "set_membership", set_membership)
    monkeypatch.setattr(auth.auth_service, "create_user", create_user)

    auth.bootstrap_admin()

    set_membership.assert_called_once_with(
        user_id="existing-bootstrap-user", organization_id="arcoenergy",
        roles={"administrador"}, permissions=set(ROLE_PERMISSIONS["administrador"]),
    )
    create_user.assert_not_called()
