"""Record retryable auth and throttling responses for offline US-9 actions.

Revision ID: 202611110121
Revises: 202611110120
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110121"
down_revision = "202611110120"
branch_labels = None
depends_on = None

ITERATION = "Iteración 109 · reintento de sincronización temporal · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-9").order_by(history.c.version.desc())
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
            "Respuestas HTTP 401, 408, 425, 429 y 5xx conservan la acción pendiente sin marcarla como conflicto de negocio, para permitir reintento tras renovar sesión o esperar.",
            "Un reintento explícito vuelve a enviar la misma operación idempotente; errores permanentes de validación o permiso mantienen su detalle y requieren revisión.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La frecuencia de reintentos y la experiencia de sesión vencida requieren validación en teléfonos reales con instaladores.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
