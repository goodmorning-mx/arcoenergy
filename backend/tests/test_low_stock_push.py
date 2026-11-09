from decimal import Decimal
from types import SimpleNamespace

from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, InventoryItem, PushSubscription
from fastapi import HTTPException
import pytest

from app.product_api import _queue_low_stock_alert, _validate_restock_responsible


def test_low_stock_push_fires_on_threshold_crossing_once_and_rearms(monkeypatch) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.product_api.get_settings", lambda: SimpleNamespace(web_push_vapid_secret="persistent-key"))
    with Session(engine) as db:
        item = InventoryItem(
            name="Microinversor", unit="pieza", quantity=5, minimum_quantity=3,
            restock_responsible_email="installer@example.test",
        )
        db.add_all([item, PushSubscription(
            installer_email="installer@example.test", endpoint="https://fcm.googleapis.com/push/abc",
            p256dh="p256dh", auth="auth",
        )])
        db.flush()
        tasks = BackgroundTasks()

        _queue_low_stock_alert(db, tasks, item)
        assert item.low_stock_alert_active is False
        assert tasks.tasks == []

        item.quantity = Decimal("2")
        _queue_low_stock_alert(db, tasks, item)
        assert item.low_stock_alert_active is True
        assert len(tasks.tasks) == 1
        subscriptions, payload = tasks.tasks[0].args
        assert subscriptions == [{"endpoint": "https://fcm.googleapis.com/push/abc", "p256dh": "p256dh", "auth": "auth"}]
        assert payload["title"] == "Existencia baja"
        assert "2" in payload["body"] and "3" in payload["body"]

        _queue_low_stock_alert(db, tasks, item)
        assert len(tasks.tasks) == 1

        item.quantity = Decimal("4")
        _queue_low_stock_alert(db, tasks, item)
        assert item.low_stock_alert_active is False

        item.quantity = Decimal("1")
        _queue_low_stock_alert(db, tasks, item)
        assert len(tasks.tasks) == 2


def test_restock_responsible_must_be_an_active_installer_account(monkeypatch) -> None:
    class Result:
        def __init__(self, found: bool) -> None:
            self.found = found

        def first(self):
            return ("installer@example.test",) if self.found else None

    class DB:
        def __init__(self, found: bool) -> None:
            self.found = found

        def execute(self, _query):
            return Result(self.found)

    assert _validate_restock_responsible(" Installer@Example.Test ", DB(True)) == "installer@example.test"
    with pytest.raises(HTTPException) as invalid:
        _validate_restock_responsible("inactive@example.test", DB(False))
    assert invalid.value.status_code == 422
