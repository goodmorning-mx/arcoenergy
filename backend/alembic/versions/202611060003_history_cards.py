"""Persist source-backed, append-only user story cards.

Revision ID: 202611060003
Revises: 202611060002
"""
from alembic import op
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4
import sqlalchemy as sa

revision = "202611060003"
down_revision = "202611060002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import HistoryCard
    table = HistoryCard.__table__
    bind = op.get_bind()
    table.create(bind=bind, checkfirst=True)
    data_path = Path(__file__).resolve().parents[2] / "app" / "history_card_initial.json"
    with data_path.open(encoding="utf-8") as source:
        records = json.load(source)
    now = datetime.now(timezone.utc)
    for row in records:
        row["id"] = str(uuid4())
        row["recorded_by"] = "system:initial-discovery-import"
        row["created_at"] = now
    op.bulk_insert(table, records)


def downgrade() -> None:
    op.drop_index("ix_ae_history_cards_story_id", table_name="ae_history_cards")
    op.drop_table("ae_history_cards")
