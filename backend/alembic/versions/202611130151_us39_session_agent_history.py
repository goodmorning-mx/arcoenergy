"""Record session-scoped CRM agent history behavior append-only.

Revision ID: 202611130151
Revises: 202611130150
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130151"
down_revision = "202611130150"
branch_labels = None
depends_on = None

ITERATION = "Iteración 149 · historial de chat del agente CRM en sesión · 2026-11-13"
UPDATES = {
    "US-39": (
        "El CRM restaura el hilo visible y su conversation_id al recargar la pestaña usando sessionStorage aislado por usuario; cerrar sesión elimina la entrada local. Los secretos de confirmación no se guardan y una confirmación restaurada exige solicitar una nueva vista previa.",
        "La conversación solo se conserva en la pestaña/sesión del navegador y el contexto del servidor sigue en memoria; el cierre de pestaña, reinicio de API, retención durable y política de privacidad requieren decisión antes de persistir historial a largo plazo.",
    ),
    "US-42": (
        "La Iteración 149 registra una nueva versión append-only de US-39 para el comportamiento de restauración de sesión y conserva sin cambios su relato fuente original.",
        "Falta cotejo humano de reconstrucciones/transcripciones y acordar retención de fuentes sensibles.",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criterion, unresolved) in UPDATES.items():
        latest = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if latest is None:
            continue
        acceptance = list(latest["acceptance_criteria"] or [])
        questions = list(latest["unresolved_questions"] or [])
        if criterion not in acceptance:
            acceptance.append(criterion)
        if unresolved not in questions:
            questions.append(unresolved)
        revised = dict(latest)
        revised.update({
            "id": str(uuid4()), "version": latest["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": acceptance, "unresolved_questions": questions,
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    # Story history is append-only; rollback is forward-only.
    pass
