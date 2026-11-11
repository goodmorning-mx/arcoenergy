"""Append the current portal-to-reference comparison evidence for US-37.

Revision ID: 202611110125
Revises: 202611110124
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110125"
down_revision = "202611110124"
branch_labels = None
depends_on = None

ITERATION = "Iteración 113 · comparación actual de portales para US-37 · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-37").order_by(history.c.version.desc())
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
            "La matriz de US-37 coteja el menú de referencia visible en el PDF con las secciones actuales de CRM/PWA e identifica brechas funcionales y de configuración.",
            "La revisión registra la versión viva de DEV y diferencia evidencia del código/despliegue de la inspección visual y comparación con el sistema activo de César, que continúan pendientes.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta acceso al sistema activo de César o capturas navegables para comparar pantallas y comportamiento que no aparecen en el PDF; administración debe confirmar si requiere una pantalla única de Configuración.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
