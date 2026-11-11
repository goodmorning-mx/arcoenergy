"""Record the full-router authentication contract for US-14.

Revision ID: 202611110095
Revises: 202611110094
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110095"
down_revision = "202611110094"
branch_labels = None
depends_on = None

ITERATION = "Iteración 83 · contrato de autenticación de rutas · 2026-11-11"
CRITERIA = [
    "Cada ruta HTTP de producto exige un token Bearer autenticado, excepto los endpoints explícitamente públicos de recepción de prospectos y chat público del agente.",
    "Una prueba de contrato inspecciona todas las rutas del API para impedir que una futura ruta omita autenticación por accidente.",
]
QUESTIONS = [
    "Falta validar con cuentas reales de los cinco roles la matriz funcional de permisos por entidad, acción y campo.",
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
