"""Support general and project expenses with an accounting date.

Revision ID: 202611060006
Revises: 202611060005
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060006"
down_revision = "202611060005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ae_expenses" not in inspector.get_table_names():
        return
    columns = {column["name"]: column for column in inspector.get_columns("ae_expenses")}
    if "occurred_on" not in columns:
        op.add_column("ae_expenses", sa.Column("occurred_on", sa.Date(), nullable=True))
        op.execute(sa.text("UPDATE ae_expenses SET occurred_on = CAST(created_at AS DATE) WHERE occurred_on IS NULL"))
        op.alter_column("ae_expenses", "occurred_on", nullable=False, server_default=sa.func.current_date())
    if "installation_id" in columns and not columns["installation_id"]["nullable"]:
        op.alter_column("ae_expenses", "installation_id", existing_type=sa.String(36), nullable=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ae_expenses" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("ae_expenses")}
    if "occurred_on" in columns:
        op.drop_column("ae_expenses", "occurred_on")
    # The optional project link is intentionally retained to avoid data loss.
