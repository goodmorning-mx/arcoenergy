"""Business calendar helpers shared by API accounting and reminders."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


BUSINESS_TIMEZONE = ZoneInfo("America/Cancun")


def business_today(now: datetime | None = None) -> date:
    """Return today's date in the product's current business calendar."""
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return instant.astimezone(BUSINESS_TIMEZONE).date()
