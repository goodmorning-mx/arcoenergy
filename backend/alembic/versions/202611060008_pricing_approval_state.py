"""Replace demo flags with an explicit commercial pricing approval state.

Revision ID: 202611060008
Revises: 202611060007
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060008"
down_revision = "202611060007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("ae_quote_packages", "ae_quotes"):
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
        if "is_demo" not in columns:
            continue
        if "pricing_approved" in columns:
            # A fresh install creates current models in the base migration,
            # then migration 001 adds its historical flag. Keep current state.
            op.drop_column(table, "is_demo")
            continue
        op.add_column(table, sa.Column("pricing_approved", sa.Boolean(), nullable=True))
        op.execute(sa.text(
            f"UPDATE {table} SET pricing_approved = CASE WHEN is_demo THEN FALSE ELSE TRUE END"
        ))
        op.alter_column(table, "pricing_approved", nullable=False, server_default=sa.false())
        op.drop_column(table, "is_demo")


def downgrade() -> None:
    for table in ("ae_quote_packages", "ae_quotes"):
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
        if "pricing_approved" not in columns or "is_demo" in columns:
            continue
        op.add_column(table, sa.Column("is_demo", sa.Boolean(), nullable=True))
        op.execute(sa.text(
            f"UPDATE {table} SET is_demo = CASE WHEN pricing_approved THEN FALSE ELSE TRUE END"
        ))
        op.alter_column(table, "is_demo", nullable=False, server_default=sa.false())
        op.drop_column(table, "pricing_approved")
