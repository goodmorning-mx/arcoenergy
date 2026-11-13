"""Record field-action retry after renewing an expired session.

Revision ID: 202611130144
Revises: 202611130143
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130144"
down_revision = "202611130143"
branch_labels = None
depends_on = None
ITERATION = "Iteración 142 · reintento 401 de campo · 2026-11-13"
CARD_UPDATES = {
    "US-9": (
        "Si una operación de campo responde 401, la PWA solicita renovar la sesión y la reintenta una vez con el mismo identificador idempotente. "
        "Si la renovación, la red o el reintento no están disponibles, conserva la operación en la cola local para sincronizarla después.",
        "El flujo de renovación y reintento se comprobó en Chrome con API simulada. Falta validarlo en teléfonos de campo y con sesiones reales durante desconexiones.",
    ),
    "US-40": (
        "La app operativa intenta renovar la sesión y repetir una acción de campo rechazada por 401 sin cambiar su identificador; si no puede completarla, conserva la acción local para reintento.",
        "PWA prueba la recuperación autenticada de una acción en Chrome; faltan usuarios reales de campo/cliente y validación en teléfonos físicos.",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criterion, unresolved) in CARD_UPDATES.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        acceptance = list(original["acceptance_criteria"] or [])
        questions = list(original["unresolved_questions"] or [])
        if criterion not in acceptance:
            acceptance.append(criterion)
        if unresolved not in questions:
            questions.append(unresolved)
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": acceptance, "unresolved_questions": questions,
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
