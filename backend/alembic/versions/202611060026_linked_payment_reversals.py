"""Add append-only corrections for supplier and customer payments.

Revision ID: 202611060026
Revises: 202611060025
"""
from alembic import op
import sqlalchemy as sa


revision = "202611060026"
down_revision = "202611060025"
branch_labels = None
depends_on = None


def _add_reversal_link(table: str, constraint: str, unique: str) -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
    if "reversal_of_id" in columns:
        return
    with op.batch_alter_table(table) as batch:
        batch.add_column(sa.Column("reversal_of_id", sa.String(36), nullable=True))
        batch.create_foreign_key(constraint, table, ["reversal_of_id"], ["id"])
        batch.create_unique_constraint(unique, ["reversal_of_id"])


def upgrade() -> None:
    _add_reversal_link("ae_supplier_payments", "fk_ae_supplier_payment_reversal", "uq_ae_supplier_payment_reversal")
    _add_reversal_link("ae_customer_payments", "fk_ae_customer_payment_reversal", "uq_ae_customer_payment_reversal")


def downgrade() -> None:
    for table, constraint, unique in (
        ("ae_customer_payments", "fk_ae_customer_payment_reversal", "uq_ae_customer_payment_reversal"),
        ("ae_supplier_payments", "fk_ae_supplier_payment_reversal", "uq_ae_supplier_payment_reversal"),
    ):
        columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}
        if "reversal_of_id" in columns:
            with op.batch_alter_table(table) as batch:
                batch.drop_constraint(unique, type_="unique")
                batch.drop_constraint(constraint, type_="foreignkey")
                batch.drop_column("reversal_of_id")
