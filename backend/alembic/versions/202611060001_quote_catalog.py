"""Add editable quote catalog and preserve quote package snapshots.

Revision ID: 202611060001
Revises: 202610270001
"""
from alembic import op
import sqlalchemy as sa
from app.models import QuotePackage

revision = "202611060001"
down_revision = "202610270001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "ae_customers" in tables and "source" not in {column["name"] for column in inspector.get_columns("ae_customers")}:
        op.add_column("ae_customers", sa.Column("source", sa.String(length=40), nullable=False, server_default="crm"))
    quote_columns = {column["name"] for column in inspector.get_columns("ae_quotes")} if "ae_quotes" in tables else set()
    additions = (
        ("installation_address", sa.Text(), ""),
        ("installation_city", sa.String(length=120), ""),
        ("is_demo", sa.Boolean(), sa.true()),
        ("structure_name", sa.String(length=120), "Estructura"),
    )
    for name, type_, default in additions:
        if name not in quote_columns:
            op.add_column("ae_quotes", sa.Column(name, type_, nullable=False, server_default=default))
    QuotePackage.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    QuotePackage.__table__.drop(bind=bind, checkfirst=True)
    for name in ("is_demo", "structure_name", "installation_city", "installation_address"):
        if "ae_quotes" in tables and name in {column["name"] for column in sa.inspect(bind).get_columns("ae_quotes")}:
            op.drop_column("ae_quotes", name)
    if "ae_customers" in tables and "source" in {column["name"] for column in sa.inspect(bind).get_columns("ae_customers")}:
        op.drop_column("ae_customers", "source")
