"""Add private Drive receipt metadata to project expenses.

Revision ID: 202611080069
Revises: 202611080068
"""
from alembic import op
import sqlalchemy as sa


revision = "202611080069"
down_revision = "202611080068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ae_expenses", sa.Column("receipt_drive_file_id", sa.String(length=200), nullable=False, server_default=""))
    op.add_column("ae_expenses", sa.Column("receipt_filename", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("ae_expenses", sa.Column("receipt_content_type", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("ae_expenses", sa.Column("receipt_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("ae_expenses", "receipt_updated_at")
    op.drop_column("ae_expenses", "receipt_content_type")
    op.drop_column("ae_expenses", "receipt_filename")
    op.drop_column("ae_expenses", "receipt_drive_file_id")
