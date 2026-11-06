"""Add searchable product details and optional supplier/barcode links.

Revision ID: 202611060024
Revises: 202611060023
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060024"
down_revision = "202611060023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("ae_inventory") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("category", sa.String(length=100), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("brand", sa.String(length=100), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("model", sa.String(length=120), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("supplier_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("barcode", sa.String(length=120), nullable=True))
        batch_op.create_foreign_key("fk_ae_inventory_supplier", "ae_suppliers", ["supplier_id"], ["id"])
        batch_op.create_index("ix_ae_inventory_supplier_id", ["supplier_id"])
    op.create_index("uq_ae_inventory_barcode", "ae_inventory", ["barcode"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_ae_inventory_barcode", table_name="ae_inventory")
    op.drop_index("ix_ae_inventory_supplier_id", table_name="ae_inventory")
    op.drop_constraint("fk_ae_inventory_supplier", "ae_inventory", type_="foreignkey")
    for column in ("barcode", "supplier_id", "model", "brand", "category", "description"):
        op.drop_column("ae_inventory", column)
