"""Link paid operating expenses to their cash or bank account.

Revision ID: 202611060010
Revises: 202611060009
"""
from alembic import op
import sqlalchemy as sa


revision = "202611060010"
down_revision = "202611060009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_expenses")}
    if "account_id" not in columns:
        op.add_column("ae_expenses", sa.Column("account_id", sa.String(36), nullable=True))
        op.create_foreign_key(
            "fk_ae_expenses_account_id_ae_financial_accounts",
            "ae_expenses", "ae_financial_accounts", ["account_id"], ["id"],
        )
        op.create_index("ix_ae_expenses_account_id", "ae_expenses", ["account_id"])


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_expenses")}
    if "account_id" in columns:
        op.drop_index("ix_ae_expenses_account_id", table_name="ae_expenses")
        op.drop_constraint("fk_ae_expenses_account_id_ae_financial_accounts", "ae_expenses", type_="foreignkey")
        op.drop_column("ae_expenses", "account_id")
