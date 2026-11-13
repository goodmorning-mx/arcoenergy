"""Record the requested DEV users and active role memberships for US-14.

Revision ID: 202611130147
Revises: 202611130146
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130147"
down_revision = "202611130146"
branch_labels = None
depends_on = None
ITERATION = "Iteración 145 · verificación de cuentas y roles DEV · 2026-11-13"
ACCEPTANCE_CRITERION = (
    "PostgreSQL DEV confirma activas las cuentas solicitadas con la membresía correcta: josue.agundiz@arcoenergy.mx administrador, "
    "elder.gonzalez@arcoenergy.mx marketing y mario.guerrero@arcoenergy.mx contador. La verificación consulta correo, rol y estado activo, sin leer ni registrar credenciales."
)


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-14").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    acceptance = list(original["acceptance_criteria"] or [])
    if ACCEPTANCE_CRITERION not in acceptance:
        acceptance.append(ACCEPTANCE_CRITERION)
    revised.update({
        "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": acceptance,
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
