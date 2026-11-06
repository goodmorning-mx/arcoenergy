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
    # The initial domain migration calls Base.metadata.create_all() using the
    # models available at runtime. On databases initialized from a newer image,
    # these columns and indexes therefore already exist before this revision.
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("ae_inventory")}
    for column in (
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("brand", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("supplier_id", sa.String(length=36), nullable=True),
        sa.Column("barcode", sa.String(length=120), nullable=True),
    ):
        if column.name not in columns:
            op.add_column("ae_inventory", column)

    inspector = sa.inspect(op.get_bind())
    foreign_keys = inspector.get_foreign_keys("ae_inventory")
    has_supplier_fk = any(
        foreign_key.get("referred_table") == "ae_suppliers"
        and foreign_key.get("constrained_columns") == ["supplier_id"]
        and foreign_key.get("referred_columns") == ["id"]
        for foreign_key in foreign_keys
    )
    if not has_supplier_fk:
        op.create_foreign_key(
            "fk_ae_inventory_supplier", "ae_inventory", "ae_suppliers", ["supplier_id"], ["id"]
        )

    indexes = {index["name"] for index in inspector.get_indexes("ae_inventory")}
    if "ix_ae_inventory_supplier_id" not in indexes:
        op.create_index("ix_ae_inventory_supplier_id", "ae_inventory", ["supplier_id"])
    if "uq_ae_inventory_barcode" not in indexes:
        op.create_index("uq_ae_inventory_barcode", "ae_inventory", ["barcode"], unique=True)


def downgrade() -> None:
    # The initial domain migration builds these fields from the live ORM model,
    # so removing them here would break databases that already had them before
    # this revision was applied. Keep the downgrade schema-preserving.
    pass
