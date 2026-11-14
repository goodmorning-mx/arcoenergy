"""Add durable confirmed CRM agent intents and idempotent follow-up writes.

Revision ID: 202611130149
Revises: 202611130148
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130149"
down_revision = "202611130148"
branch_labels = None
depends_on = None

ITERATION = "Iteración 147 · acción confirmada de agente CRM · 2026-11-13"
US43_CRITERION = (
    "El agente CRM puede proponer un seguimiento para un cliente con nombre exacto, fecha y nota; muestra un resumen al usuario, "
    "requiere confirmación explícita, vuelve a verificar el permiso vigente y guarda la actividad una sola vez con bitácora."
)
US43_UNRESOLVED = (
    "El primer comando confirmado cubre programación de seguimientos. Falta acordar y construir los demás módulos/operaciones prioritarios "
    "y validar con stakeholders el alcance de datos personales que procesa el proveedor del modelo."
)


def _append_card_update(bind, history, story_id: str, criterion: str, unresolved: str | None = None) -> None:
    original = bind.execute(
        sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    acceptance = list(original["acceptance_criteria"] or [])
    questions = list(original["unresolved_questions"] or [])
    if criterion not in acceptance:
        acceptance.append(criterion)
    if unresolved and unresolved not in questions:
        questions.append(unresolved)
    revised = dict(original)
    revised.update({
        "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": acceptance, "unresolved_questions": questions,
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def upgrade() -> None:
    op.create_table(
        "ae_agent_action_intents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(80), nullable=False),
        sa.Column("user_id", sa.String(80), nullable=False),
        sa.Column("conversation_id", sa.String(80), nullable=False),
        sa.Column("tool_name", sa.String(160), nullable=False),
        sa.Column("arguments_hash", sa.String(64), nullable=False),
        sa.Column("confirmation_token_hash", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(36), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ae_agent_action_intents_organization_id", "ae_agent_action_intents", ["organization_id"])
    op.create_index("ix_ae_agent_action_intents_user_id", "ae_agent_action_intents", ["user_id"])
    op.add_column("ae_followups", sa.Column("agent_intent_id", sa.String(36), nullable=True))
    op.create_index("uq_ae_followups_agent_intent_id", "ae_followups", ["agent_intent_id"], unique=True)

    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    _append_card_update(bind, history, "US-43", US43_CRITERION, US43_UNRESOLVED)


def downgrade() -> None:
    op.drop_index("uq_ae_followups_agent_intent_id", table_name="ae_followups")
    op.drop_column("ae_followups", "agent_intent_id")
    op.drop_index("ix_ae_agent_action_intents_user_id", table_name="ae_agent_action_intents")
    op.drop_index("ix_ae_agent_action_intents_organization_id", table_name="ae_agent_action_intents")
    op.drop_table("ae_agent_action_intents")
