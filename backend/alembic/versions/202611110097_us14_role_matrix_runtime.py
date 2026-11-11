"""Record runtime coverage of role permissions for US-14.

Revision ID: 202611110097
Revises: 202611110096
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110097"
down_revision = "202611110096"
branch_labels = None
depends_on = None

ITERATION = "Iteración 85 · matriz runtime de roles · 2026-11-11"
CRITERIA = [
    "La prueba de membresía recorre los cinco roles y cada permiso del catálogo: concede todos los permisos vigentes del rol y rechaza los ausentes con 403.",
    "Cada endpoint privado enlaza autenticación Bearer con un guard require_permissions o require_any_permission; solo el prospecto público y el chat público del agente quedan fuera de la matriz.",
]
QUESTIONS = [
    "La matriz técnica está probada con membresías aisladas; el responsable de ArcoEnergy todavía debe validar con sus cuentas reales si el alcance de cada rol coincide con sus funciones.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-14")
        .order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"], *CRITERIA],
        "unresolved_questions": [*original["unresolved_questions"], *QUESTIONS],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
