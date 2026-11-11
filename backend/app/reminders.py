"""Background delivery for CRM follow-up reminders."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import or_, select, update

from app.config import get_settings
from app.models import FollowUp, PushSubscription
from app.time_utils import business_today

logger = logging.getLogger(__name__)


def send_due_followup_pushes(
    owner_email: str | None = None,
    *,
    session_factory=None,
    push_delivery=None,
    today: date | None = None,
    sent_at: datetime | None = None,
) -> int:
    """Send once to each responsible user's subscribed devices when a follow-up is due."""
    settings = get_settings()
    if not settings.web_push_vapid_secret:
        return 0

    if session_factory is None or push_delivery is None:
        # Resolve product API objects lazily so its router can also import this module.
        from app.product_api import SessionLocal, _deliver_push_payload

        session_factory = session_factory or SessionLocal
        push_delivery = push_delivery or _deliver_push_payload

    local_today = today or business_today()
    timestamp = sent_at or datetime.now(timezone.utc)
    stale_claim_before = timestamp - timedelta(minutes=10)
    target_email = owner_email.strip().lower() if owner_email else None
    sent_count = 0

    with session_factory() as db:
        query = select(FollowUp).where(
            FollowUp.done.is_(False),
            FollowUp.due_date <= local_today,
            FollowUp.push_notified_at.is_(None),
            or_(FollowUp.push_claimed_at.is_(None), FollowUp.push_claimed_at < stale_claim_before),
            FollowUp.assigned_to != "",
        ).order_by(FollowUp.due_date, FollowUp.id)
        if target_email:
            query = query.where(FollowUp.assigned_to == target_email)

        for followup in db.scalars(query).all():
            email = followup.assigned_to.strip().lower()
            subscriptions = db.scalars(
                select(PushSubscription).where(PushSubscription.user_email == email)
            ).all()
            if not subscriptions:
                continue

            claimed = db.execute(
                update(FollowUp)
                .where(
                    FollowUp.id == followup.id,
                    FollowUp.done.is_(False),
                    FollowUp.push_notified_at.is_(None),
                    or_(FollowUp.push_claimed_at.is_(None), FollowUp.push_claimed_at < stale_claim_before),
                )
                .values(push_claimed_at=timestamp)
                .execution_options(synchronize_session=False)
            )
            if claimed.rowcount != 1:
                db.rollback()
                continue
            db.commit()

            payload = {
                "title": "Seguimiento pendiente",
                "body": "Tienes un contacto programado para hoy o vencido. Abre ArcoEnergy para revisar tu agenda.",
                "url": "/crm/",
                "tag": f"arcoenergy-followup-{followup.id}",
            }
            recipients = [
                {"endpoint": row.endpoint, "p256dh": row.p256dh, "auth": row.auth}
                for row in subscriptions
            ]
            try:
                delivered = bool(push_delivery(recipients, payload))
            except Exception:
                logger.exception("Follow-up reminder push failed")
                delivered = False
            if delivered:
                sent_count += 1
                db.execute(
                    update(FollowUp)
                    .where(FollowUp.id == followup.id, FollowUp.push_claimed_at == timestamp)
                    .values(push_notified_at=timestamp, push_claimed_at=None)
                    .execution_options(synchronize_session=False)
                )
                db.commit()
            else:
                # The claim expires after ten minutes if a process crashes mid-delivery.
                db.execute(
                    update(FollowUp)
                    .where(FollowUp.id == followup.id, FollowUp.push_claimed_at == timestamp)
                    .values(push_claimed_at=None)
                    .execution_options(synchronize_session=False)
                )
                db.commit()

    return sent_count


async def followup_push_loop() -> None:
    """Poll durable follow-up rows so reminders survive API restarts."""
    while True:
        try:
            await asyncio.to_thread(send_due_followup_pushes)
        except Exception:
            logger.exception("Follow-up reminder delivery cycle failed")
        await asyncio.sleep(60)
