"""Persist source-backed, append-only user story cards.

Revision ID: 202611060003
Revises: 202611060002
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060003"
down_revision = "202611060002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import HistoryCard
    HistoryCard.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.drop_index("ix_ae_history_cards_story_id", table_name="ae_history_cards")
    op.drop_table("ae_history_cards")
