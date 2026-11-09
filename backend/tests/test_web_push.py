from unittest.mock import Mock, patch
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, PushSubscription
from app import product_api
from app.product_api import PushSubscriptionDeleteInput, PushSubscriptionInput, _queue_installation_push, remove_push_subscription, save_push_subscription
from app.web_push import _NoRedirectSession, send_push, validate_push_endpoint, vapid_public_key
from gm_auth.models import AuthIdentity


def test_vapid_public_key_is_stable_and_secret_specific():
    assert vapid_public_key("factory-generated-secret") == vapid_public_key("factory-generated-secret")
    assert vapid_public_key("factory-generated-secret") != vapid_public_key("another-secret")
    assert len(vapid_public_key("factory-generated-secret")) == 87


@pytest.mark.parametrize("endpoint", [
    "http://fcm.googleapis.com/send/abc",
    "https://localhost/push",
    "https://127.0.0.1/push",
    "https://attacker.example/push",
    "https://fcm.googleapis.com.evil.example/push",
    "https://user@fcm.googleapis.com/push",
    "https://fcm.googleapis.com:8443/push",
])
def test_push_endpoint_rejects_untrusted_or_unsafe_urls(endpoint):
    with pytest.raises(ValueError):
        validate_push_endpoint(endpoint)


@pytest.mark.parametrize("endpoint", [
    "https://fcm.googleapis.com/fcm/send/abc",
    "https://updates.push.services.mozilla.com/wpush/v2/abc",
    "https://web.push.apple.com/Qwerty",
])
def test_push_endpoint_allows_known_push_services(endpoint):
    assert validate_push_endpoint(endpoint) == endpoint


def test_push_http_client_never_follows_redirects():
    with patch("requests.Session.request", return_value=Mock()) as request:
        session = _NoRedirectSession()
        session.request("POST", "https://fcm.googleapis.com/push", allow_redirects=True)
    assert request.call_args.kwargs["allow_redirects"] is False


def test_send_push_uses_configured_vapid_and_encrypted_subscription():
    response = Mock(status_code=201)
    subscription = {"endpoint": "https://fcm.googleapis.com/fcm/send/abc", "p256dh": "public", "auth": "secret"}
    payload = {"title": "Nueva instalación asignada", "body": "Orden AE-OT-1", "url": "/app/"}
    with patch("app.web_push.webpush", return_value=response) as send:
        assert send_push(subscription, payload, "stable-secret", "mailto:admin@arcoenergy.mx") == 201
    kwargs = send.call_args.kwargs
    assert kwargs["subscription_info"] == {"endpoint": subscription["endpoint"], "keys": {"p256dh": "public", "auth": "secret"}}
    assert kwargs["vapid_claims"] == {"sub": "mailto:admin@arcoenergy.mx"}
    assert '"url":"/app/"' in kwargs["data"]


def test_only_installer_can_store_and_remove_own_push_subscription(monkeypatch):
    monkeypatch.setattr(product_api, "get_settings", lambda: SimpleNamespace(web_push_vapid_secret="server-secret"))
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity("installer-id", "arcoenergy", frozenset({"instalador"}), frozenset({"installations:read"}), "crew@example.test", "Installer")
    administrator = AuthIdentity("admin-id", "arcoenergy", frozenset({"administrador"}), frozenset({"installations:read"}), "admin@example.test", "Admin")
    endpoint = "https://fcm.googleapis.com/fcm/send/push-token"
    body = PushSubscriptionInput(endpoint=endpoint, keys={"p256dh": "device-key", "auth": "auth-key"})
    with Session(engine) as db:
        with pytest.raises(HTTPException) as denied:
            save_push_subscription(body, administrator, db)
        assert denied.value.status_code == 403

        save_push_subscription(body, installer, db)
        saved = db.scalars(select(PushSubscription)).one()
        assert saved.installer_email == "crew@example.test"
        assert saved.p256dh == "device-key"

        with pytest.raises(HTTPException) as denied:
            remove_push_subscription(PushSubscriptionDeleteInput(endpoint=endpoint), administrator, db)
        assert denied.value.status_code == 403
        assert db.scalars(select(PushSubscription)).one().endpoint == endpoint
        remove_push_subscription(PushSubscriptionDeleteInput(endpoint=endpoint), installer, db)
        assert db.scalars(select(PushSubscription)).all() == []


def test_assignment_schedules_push_only_for_subscribed_installers(monkeypatch):
    monkeypatch.setattr(product_api, "get_settings", lambda: SimpleNamespace(web_push_vapid_secret="server-secret"))
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            PushSubscription(installer_email="one@example.test", endpoint="https://fcm.googleapis.com/push/1", p256dh="key-1", auth="auth-1"),
            PushSubscription(installer_email="other@example.test", endpoint="https://fcm.googleapis.com/push/2", p256dh="key-2", auth="auth-2"),
        ])
        db.commit()
        tasks = BackgroundTasks()
        _queue_installation_push(db, tasks, ["one@example.test"], "AE-OT-2026-00001")

    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].args[0] == [{
        "endpoint": "https://fcm.googleapis.com/push/1", "p256dh": "key-1", "auth": "auth-1",
    }]
    assert tasks.tasks[0].args[1] == "AE-OT-2026-00001"
