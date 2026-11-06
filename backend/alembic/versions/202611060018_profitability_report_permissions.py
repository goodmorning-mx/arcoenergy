"""Grant the preliminary profitability report to accounting administrators.

Revision ID: 202611060018
Revises: 202611060017
"""
from alembic import op
import sqlalchemy as sa

revision = "202611060018"
down_revision = "202611060017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    memberships = sa.Table("gm_auth_memberships", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(sa.select(memberships.c.user_id, memberships.c.organization_id, memberships.c.roles, memberships.c.permissions)).mappings():
        roles = {role.strip().lower() for role in (row["roles"] or [])}
        if roles & {"admin", "administrador", "contador", "finanzas"}:
            permissions = sorted(set(row["permissions"] or []) | {"reports:read"})
            bind.execute(sa.update(memberships).where(
                memberships.c.user_id == row["user_id"],
                memberships.c.organization_id == row["organization_id"],
            ).values(permissions=permissions))


def downgrade() -> None:
    # Role grants may also have been explicitly assigned after this migration.
    # Keep permission rows intact; the application route is removed with its code.
    pass
