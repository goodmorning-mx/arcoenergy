"""Add movement kind and cost snapshots for inventory history.

Revision ID: 202611060004
Revises: 202611060003
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060004"
down_revision = "202611060003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ae_inventory_movements" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("ae_inventory_movements")}
    if "movement_type" not in columns:
        op.add_column(
            "ae_inventory_movements",
            sa.Column("movement_type", sa.String(20), nullable=False, server_default="in"),
        )
    if "unit_cost" not in columns:
        op.add_column(
            "ae_inventory_movements",
            sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        )
    bind = op.get_bind()
    bind.execute(sa.text("""
        UPDATE ae_inventory_movements
        SET movement_type = CASE
            WHEN installation_id IS NOT NULL THEN 'out'
            WHEN lower(reason) LIKE '%merma%' OR lower(reason) LIKE '%dañad%' THEN 'waste'
            ELSE 'in'
        END
        WHERE movement_type = 'in'
    """))
def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "ae_inventory_movements" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("ae_inventory_movements")}
    if "unit_cost" in columns:
        op.drop_column("ae_inventory_movements", "unit_cost")
    if "movement_type" in columns:
        op.drop_column("ae_inventory_movements", "movement_type")
