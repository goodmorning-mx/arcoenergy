"""Record protected PWA/CRM login redirect verification for US-14.

Revision ID: 202611110133
Revises: 202611110132
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110133"
down_revision = "202611110132"
branch_labels = None
depends_on = None

ITERATION = "Iteración 121 · redirección de superficies protegidas al login · 2026-11-11"


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
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "La prueba de Chrome abre /app/ y /crm/ sin sesión y verifica que ambas superficies muestran el formulario de inicio de sesión.",
            "Las rutas /app/login, /crm/login y el alias /login continúan renderizando el acceso real sin usuarios demo.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta validar con cuentas reales el alcance de cada rol y el aislamiento de clientes e instaladores asignados.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
