"""Capture the embedded CRM agent operations requirement as US-43.

Revision ID: 202611130148
Revises: 202611130147
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130148"
down_revision = "202611130147"
branch_labels = None
depends_on = None

ITERATION = "Iteración 146 · agente CRM operativo · 2026-11-13"
SOURCE_LITERAL = (
    "ademas muy importante va a ser agentico quiere decir que probablemente tenga a la derecha el chat incrustado "
    "que hace operaciones via agent de nuestros modulos porque ademas dale una revisada a nuestros modulos gm-* "
    "que estan en nuestra cuenta de github para que entiendas"
)
INITIAL_CARD = {
    "story_id": "US-43",
    "version": 1,
    "iteration": ITERATION,
    "stakeholder": "Dueño del producto (nombre no registrado)",
    "source_literal": SOURCE_LITERAL,
    "source_type": "Conversación del proyecto",
    "source_reference": "docs/discovery/sources/owner-agentic-crm-requirement.md",
    "source_artifact": {"path": "docs/discovery/sources/owner-agentic-crm-requirement.md", "kind": "conversation-transcription"},
    "source_language": "es",
    "source_attribution": "Dueño del producto Arco Energy",
    "source_occurred_at": None,
    "source_confidence": "literal_user_message",
    "source_links": [],
    "normalized_story": "Como integrante del equipo con permisos autorizados, quiero pedir operaciones del negocio desde el chat del CRM y que el agente las ejecute mediante los módulos gm-* para trabajar con lenguaje natural.",
    "acceptance_criteria": [
        "El chat integrado del CRM puede invocar herramientas de negocio ofrecidas por módulos gm-*.",
        "Cada operación consulta los permisos y la membresía vigentes del usuario autenticado.",
        "El agente presenta y requiere confirmación explícita antes de ejecutar una mutación; el resultado deja evidencia auditable.",
        "El agente público de cotización permanece separado y de solo lectura; no hereda herramientas internas del CRM.",
    ],
    "unresolved_questions": [
        "Stakeholders deben priorizar las operaciones iniciales, confirmar qué datos se pueden enviar al modelo y revisar el flujo de confirmación para cada tipo de operación.",
    ],
    "linked_cards": ["US-4", "US-14", "US-39", "US-41"],
    "recorded_by": "system:implementation-iteration",
}

US42_AUDIT = (
    "La Iteración 146 registra US-43 como una nueva tarjeta basada en el requisito literal del dueño sobre operaciones CRM mediante agentes gm-*. "
    "La auditoría actualizada contiene 43 tarjetas distintas y conserva sus relatos fuente en el historial append-only.",
    "Falta acordar el catálogo de operaciones del agente CRM, el alcance de datos permitido para el modelo y validar confirmaciones con los stakeholders.",
)


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    existing = bind.execute(
        sa.select(history.c.id).where(history.c.story_id == "US-43").limit(1)
    ).first()
    if existing is None:
        bind.execute(history.insert().values(**{
            **INITIAL_CARD,
            "id": str(uuid4()),
            "created_at": datetime.now(timezone.utc),
        }))

    latest = bind.execute(
        sa.select(history).where(history.c.story_id == "US-42").order_by(history.c.version.desc())
    ).mappings().first()
    if latest is not None:
        acceptance = list(latest["acceptance_criteria"] or [])
        questions = list(latest["unresolved_questions"] or [])
        criterion, unresolved = US42_AUDIT
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
    pass
