"""Record supplier purchases, stock receipts and linked supplier payments.

Revision ID: 202611060009
Revises: 202611060008
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060009"
down_revision = "202611060008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import Purchase, PurchaseLine, SupplierPayment
    bind = op.get_bind()
    Purchase.__table__.create(bind=bind, checkfirst=True)
    PurchaseLine.__table__.create(bind=bind, checkfirst=True)
    SupplierPayment.__table__.create(bind=bind, checkfirst=True)
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_inventory_movements")}
    if "purchase_line_id" not in columns:
        op.add_column("ae_inventory_movements", sa.Column("purchase_line_id", sa.String(36), nullable=True))
        op.create_foreign_key(
            "fk_ae_inventory_movements_purchase_line_id_ae_purchase_lines",
            "ae_inventory_movements", "ae_purchase_lines", ["purchase_line_id"], ["id"],
        )
        op.create_index("ix_ae_inventory_movements_purchase_line_id", "ae_inventory_movements", ["purchase_line_id"])
    op.execute("CREATE SEQUENCE IF NOT EXISTS ae_purchase_folio_seq START WITH 1")


def downgrade() -> None:
    from app.models import Purchase, PurchaseLine, SupplierPayment
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_inventory_movements")}
    if "purchase_line_id" in columns:
        op.drop_index("ix_ae_inventory_movements_purchase_line_id", table_name="ae_inventory_movements")
        op.drop_constraint("fk_ae_inventory_movements_purchase_line_id_ae_purchase_lines", "ae_inventory_movements", type_="foreignkey")
        op.drop_column("ae_inventory_movements", "purchase_line_id")
    SupplierPayment.__table__.drop(bind=bind, checkfirst=True)
    PurchaseLine.__table__.drop(bind=bind, checkfirst=True)
    Purchase.__table__.drop(bind=bind, checkfirst=True)
    op.execute("DROP SEQUENCE IF EXISTS ae_purchase_folio_seq")
