"""Link returned stock to its original installation issue.

Revision ID: 202611060005
Revises: 202611060004
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060005"
down_revision = "202611060004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ae_inventory_movements" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("ae_inventory_movements")}
    if "related_movement_id" not in columns:
        op.add_column("ae_inventory_movements", sa.Column("related_movement_id", sa.String(36), nullable=True))
        op.create_index("ix_ae_inventory_movements_related_movement_id", "ae_inventory_movements", ["related_movement_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ae_inventory_movements" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("ae_inventory_movements")}
    if "related_movement_id" in columns:
        indexes = {index["name"] for index in inspector.get_indexes("ae_inventory_movements")}
        if "ix_ae_inventory_movements_related_movement_id" in indexes:
            op.drop_index("ix_ae_inventory_movements_related_movement_id", table_name="ae_inventory_movements")
        op.drop_column("ae_inventory_movements", "related_movement_id")
