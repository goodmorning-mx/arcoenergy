"""Link receivable payments to customer balances and cash accounts.

Revision ID: 202611060011
Revises: 202611060010
"""
from alembic import op


revision = "202611060011"
down_revision = "202611060010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import CustomerPayment
    CustomerPayment.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    from app.models import CustomerPayment
    CustomerPayment.__table__.drop(bind=op.get_bind(), checkfirst=True)
