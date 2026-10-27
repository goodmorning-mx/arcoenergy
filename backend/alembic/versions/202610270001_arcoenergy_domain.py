"""Create ArcoEnergy CRM and operations data tables.

Revision ID: 202610270001
Revises: 202607150001
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from alembic import op
from gm_auth.models import metadata as auth_metadata

from app.models import Base

revision = "202610270001"
down_revision = "202607150001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS ae_quote_folio_seq START WITH 1")
    bind = op.get_bind()
    auth_metadata.create_all(bind=bind)
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
    auth_metadata.drop_all(bind=bind)
    op.execute("DROP SEQUENCE IF EXISTS ae_quote_folio_seq")
