from datetime import datetime, timezone
import pytest

from app import time_utils
from app.models import FinancialAccount, Purchase
from app.product_api import CashMovementInput, PaymentInput


def test_business_today_uses_cancun_timezone_when_utc_is_next_day() -> None:
    assert time_utils.business_today(datetime(2026, 11, 11, 4, 30, tzinfo=timezone.utc)).isoformat() == "2026-11-10"


def test_business_today_advances_at_cancun_midnight() -> None:
    assert time_utils.business_today(datetime(2026, 11, 11, 5, 30, tzinfo=timezone.utc)).isoformat() == "2026-11-11"


def test_business_today_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        time_utils.business_today(datetime(2026, 11, 11, 4, 30))


def test_financial_model_and_request_defaults_share_business_today() -> None:
    defaults = [
        FinancialAccount.__table__.c.opening_balance_date.default.arg,
        Purchase.__table__.c.purchase_date.default.arg,
        CashMovementInput.model_fields["occurred_on"].default_factory,
        PaymentInput.model_fields["paid_on"].default_factory,
    ]
    assert all(default.__name__ == "business_today" for default in defaults)
    assert all(default.__module__.endswith("time_utils") for default in defaults)
