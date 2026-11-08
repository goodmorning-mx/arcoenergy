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
    # The initial domain migration creates tables from the current ORM model.
    # On a fresh database these columns already exist before this revision runs.
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_expenses")}
    for column in (
        sa.Column("receipt_drive_file_id", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("receipt_filename", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("receipt_content_type", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("receipt_updated_at", sa.DateTime(timezone=True), nullable=True),
    ):
        if column.name not in existing:
            op.add_column("ae_expenses", column)


def downgrade() -> None:
    # The base domain revision creates current ORM columns; dropping them would
    # break schema consistency on a fresh installation.
    pass
