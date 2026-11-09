from datetime import date, datetime, timezone
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, FollowUp, PushSubscription
from app import reminders


def make_session_factory():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_due_followup_push_is_private_scoped_and_sent_once(monkeypatch):
    monkeypatch.setattr(reminders, "get_settings", lambda: SimpleNamespace(web_push_vapid_secret="configured"))
    engine, session_factory = make_session_factory()
    due = FollowUp(customer_id="customer-secret", due_date=date(2026, 11, 9), note="cliente espera descuento", assigned_to="seller@example.test")
    not_due = FollowUp(customer_id="another-customer", due_date=date(2026, 11, 10), assigned_to="seller@example.test")
    with session_factory() as db:
        db.add_all([
            due,
            not_due,
            PushSubscription(user_email="seller@example.test", endpoint="https://fcm.googleapis.com/push/seller", p256dh="key", auth="auth"),
            PushSubscription(user_email="other@example.test", endpoint="https://fcm.googleapis.com/push/other", p256dh="key", auth="auth"),
        ])
        db.commit()

    deliveries = []
    def deliver(subscriptions, payload):
        deliveries.append((subscriptions, payload))
        return True

    sent_at = datetime(2026, 11, 9, 15, tzinfo=timezone.utc)
    assert reminders.send_due_followup_pushes(
        session_factory=session_factory,
        push_delivery=deliver,
        today=date(2026, 11, 9),
        sent_at=sent_at,
    ) == 1
    assert len(deliveries) == 1
    subscriptions, payload = deliveries[0]
    assert [subscription["endpoint"] for subscription in subscriptions] == ["https://fcm.googleapis.com/push/seller"]
    assert payload == {
        "title": "Seguimiento pendiente",
        "body": "Tienes un contacto programado para hoy o vencido. Abre ArcoEnergy para revisar tu agenda.",
        "url": "/crm/",
        "tag": f"arcoenergy-followup-{due.id}",
    }
    assert "cliente espera descuento" not in str(payload)
    assert "customer-secret" not in str(payload)
    with session_factory() as db:
        stored_due = db.get(FollowUp, due.id)
        stored_future = db.get(FollowUp, not_due.id)
        assert stored_due.push_notified_at.replace(tzinfo=timezone.utc) == sent_at
        assert stored_due.push_claimed_at is None
        assert stored_future.push_notified_at is None
        assert stored_future.push_claimed_at is None

    assert reminders.send_due_followup_pushes(
        session_factory=session_factory, push_delivery=deliver, today=date(2026, 11, 9), sent_at=sent_at,
    ) == 0
    assert len(deliveries) == 1
    engine.dispose()


def test_push_failure_retries_after_subscription_is_added(monkeypatch):
    monkeypatch.setattr(reminders, "get_settings", lambda: SimpleNamespace(web_push_vapid_secret="configured"))
    engine, session_factory = make_session_factory()
    due = FollowUp(customer_id="customer", due_date=date(2026, 11, 9), assigned_to="seller@example.test")
    with session_factory() as db:
        db.add(due)
        db.commit()

    # Without an opt-in device there is no claim, so a later subscription can receive the reminder.
    assert reminders.send_due_followup_pushes(session_factory=session_factory, push_delivery=lambda *_: True, today=date(2026, 11, 9)) == 0
    with session_factory() as db:
        db.add(PushSubscription(user_email="seller@example.test", endpoint="https://fcm.googleapis.com/push/seller", p256dh="key", auth="auth"))
        db.commit()

    attempts = iter([False, True])
    deliver = lambda *_: next(attempts)
    assert reminders.send_due_followup_pushes(session_factory=session_factory, push_delivery=deliver, today=date(2026, 11, 9)) == 0
    with session_factory() as db:
        assert db.get(FollowUp, due.id).push_notified_at is None
        assert db.get(FollowUp, due.id).push_claimed_at is None
    assert reminders.send_due_followup_pushes(session_factory=session_factory, push_delivery=deliver, today=date(2026, 11, 9)) == 1
    with session_factory() as db:
        assert db.get(FollowUp, due.id).push_notified_at is not None
    engine.dispose()


def test_abandoned_push_claim_can_be_recovered(monkeypatch):
    monkeypatch.setattr(reminders, "get_settings", lambda: SimpleNamespace(web_push_vapid_secret="configured"))
    engine, session_factory = make_session_factory()
    sent_at = datetime(2026, 11, 9, 15, 15, tzinfo=timezone.utc)
    due = FollowUp(
        customer_id="customer", due_date=date(2026, 11, 9), assigned_to="seller@example.test",
        push_claimed_at=datetime(2026, 11, 9, 14, 55, tzinfo=timezone.utc),
    )
    with session_factory() as db:
        db.add_all([
            due,
            PushSubscription(user_email="seller@example.test", endpoint="https://fcm.googleapis.com/push/seller", p256dh="key", auth="auth"),
        ])
        db.commit()

    deliveries = []
    assert reminders.send_due_followup_pushes(
        session_factory=session_factory,
        push_delivery=lambda subscriptions, payload: deliveries.append(payload) or True,
        today=date(2026, 11, 9),
        sent_at=sent_at,
    ) == 1
    assert len(deliveries) == 1
    with session_factory() as db:
        stored = db.get(FollowUp, due.id)
        assert stored.push_notified_at.replace(tzinfo=timezone.utc) == sent_at
        assert stored.push_claimed_at is None
    engine.dispose()
