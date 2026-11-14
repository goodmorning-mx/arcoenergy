"""Record session-scoped CRM agent history behavior append-only.

Revision ID: 202611140152
Revises: 202611130151
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611140152"
down_revision = "202611130151"
branch_labels = None
depends_on = None

ITERATION = "Iteración 150 · verificación Chrome del historial de chat CRM · 2026-11-14"
UPDATES = {
    "US-39": (
        "Chrome CI recarga el CRM con una vista previa simulada y verifica restauración del hilo, aislamiento por usuario, ausencia de tokens/credenciales en sessionStorage y ausencia del botón de ejecución para la confirmación vencida. El caso no modifica datos reales.",
        "La conversación solo se conserva en la pestaña/sesión del navegador y el contexto del servidor sigue en memoria; el cierre de pestaña, reinicio de API, retención durable y política de privacidad requieren decisión antes de persistir historial a largo plazo.",
    ),
    "US-42": (
        "La prueba Chrome de Iteración 150 valida en el CRM que el hilo de agente reaparece tras recargar, omite secretos de confirmación y deja vencido/deshabilitado el botón de ejecución; conserva el relato fuente original.",
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
