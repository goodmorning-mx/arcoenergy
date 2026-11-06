"""Create financial account, immutable cash movement and supplier registers.

Revision ID: 202611060007
Revises: 202611060006
"""
from alembic import op

revision = "202611060007"
down_revision = "202611060006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import CashMovement, FinancialAccount, Supplier
    bind = op.get_bind()
    FinancialAccount.__table__.create(bind=bind, checkfirst=True)
    CashMovement.__table__.create(bind=bind, checkfirst=True)
    Supplier.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    from app.models import CashMovement, FinancialAccount, Supplier
    bind = op.get_bind()
    Supplier.__table__.drop(bind=bind, checkfirst=True)
    CashMovement.__table__.drop(bind=bind, checkfirst=True)
    FinancialAccount.__table__.drop(bind=bind, checkfirst=True)
