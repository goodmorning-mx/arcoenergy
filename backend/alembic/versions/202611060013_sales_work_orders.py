"""Register accepted quotes as sales with materialized work orders.

Revision ID: 202611060013
Revises: 202611060012
"""
from alembic import op
import sqlalchemy as sa


revision = "202611060013"
down_revision = "202611060012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import Sale
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_installations")}
    if "folio" not in columns:
        op.add_column("ae_installations", sa.Column("folio", sa.String(36), nullable=True))
        op.create_unique_constraint("uq_ae_installations_folio", "ae_installations", ["folio"])
    Sale.__table__.create(bind=bind, checkfirst=True)
    op.execute("CREATE SEQUENCE IF NOT EXISTS ae_sale_folio_seq START WITH 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS ae_work_order_folio_seq START WITH 1")
    memberships = sa.Table("gm_auth_memberships", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(sa.select(memberships.c.user_id, memberships.c.organization_id, memberships.c.roles, memberships.c.permissions)).mappings():
        roles = {role.strip().lower() for role in (row["roles"] or [])}
        if roles & {"admin", "administrador", "contador", "finanzas"}:
            permissions = sorted(set(row["permissions"] or []) | {"sales:read", "sales:write"})
            bind.execute(sa.update(memberships).where(
                memberships.c.user_id == row["user_id"],
                memberships.c.organization_id == row["organization_id"],
            ).values(permissions=permissions))


def downgrade() -> None:
    from app.models import Sale
    bind = op.get_bind()
    Sale.__table__.drop(bind=bind, checkfirst=True)
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_installations")}
    if "folio" in columns:
        op.drop_constraint("uq_ae_installations_folio", "ae_installations", type_="unique")
        op.drop_column("ae_installations", "folio")
    op.execute("DROP SEQUENCE IF EXISTS ae_work_order_folio_seq")
    op.execute("DROP SEQUENCE IF EXISTS ae_sale_folio_seq")
