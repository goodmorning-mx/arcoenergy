import importlib.util
import json
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa
from sqlalchemy import select

from app.models import HistoryCard


ROOT = Path(__file__).resolve().parents[1]


def test_background_followup_push_migration_preserves_subscriptions_and_story_sources():
    spec = importlib.util.spec_from_file_location(
        "background_followup_push",
        ROOT / "alembic" / "versions" / "202611090076_background_followup_push.py",
    )
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = sa.create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    metadata = sa.MetaData()
    subscriptions = sa.Table(
        "ae_push_subscriptions", metadata,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("installer_email", sa.String(180), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(200), nullable=False),
        sa.Column("auth", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("endpoint", name="uq_ae_push_subscriptions_endpoint"),
    )
    followups = sa.Table(
        "ae_followups", metadata,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36), nullable=False),
        sa.Column("quote_id", sa.String(36)),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(180), nullable=False),
        sa.Column("assigned_to", sa.String(180), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    records = json.loads((ROOT / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    for row in records:
        row.update(id=str(uuid4()), recorded_by="source-import", created_at=now)
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE INDEX ix_ae_push_subscriptions_installer_email ON ae_push_subscriptions (installer_email)")
        connection.execute(HistoryCard.__table__.insert(), records)
        connection.execute(subscriptions.insert(), {
            "id": "subscription-1", "installer_email": "installer@example.test",
            "endpoint": "https://fcm.googleapis.com/push/1", "p256dh": "key", "auth": "auth", "created_at": now,
        })
        connection.execute(followups.insert(), {
            "id": "followup-1", "customer_id": "customer-1", "quote_id": None,
            "due_date": date(2026, 11, 9), "note": "Retomar", "created_by": "seller@example.test",
            "assigned_to": "seller@example.test", "done": False, "created_at": now,
        })
        original_literals = dict(connection.execute(select(HistoryCard.story_id, HistoryCard.source_literal)
            .where(HistoryCard.story_id.in_(["US-4", "US-39", "US-40"]), HistoryCard.version == 1)).all())
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        subscription_columns = {column["name"] for column in sa.inspect(connection).get_columns("ae_push_subscriptions")}
        followup_columns = {column["name"] for column in sa.inspect(connection).get_columns("ae_followups")}
        index_names = {index["name"] for index in sa.inspect(connection).get_indexes("ae_push_subscriptions")}
        stored_owner = connection.execute(sa.text("SELECT user_email FROM ae_push_subscriptions WHERE id = 'subscription-1'")).scalar_one()
        story_versions = connection.execute(select(HistoryCard.story_id, HistoryCard.version, HistoryCard.iteration, HistoryCard.source_literal)
            .where(HistoryCard.story_id.in_(list(original_literals))).order_by(HistoryCard.story_id, HistoryCard.version)).all()

    assert "installer_email" not in subscription_columns and "user_email" in subscription_columns
    assert {"push_claimed_at", "push_notified_at"} <= followup_columns
    assert "ix_ae_push_subscriptions_installer_email" not in index_names
    assert "ix_ae_push_subscriptions_user_email" in index_names
    assert stored_owner == "installer@example.test"
    assert len(story_versions) == 6
    for story_id, version, iteration, literal in story_versions:
        assert literal == original_literals[story_id]
        if version == 2:
            assert iteration == migration.ITERATION
