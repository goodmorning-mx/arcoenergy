"""Record CRM agent conversation continuity when its panel is hidden.

Revision ID: 202611110131
Revises: 202611110130
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110131"
down_revision = "202611110130"
branch_labels = None
depends_on = None

ITERATION = "Iteración 119 · continuidad del asistente del CRM · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-39")
        .order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return

    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "source_reference": f"{original['source_reference']}; continuidad del asistente CRM",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Cerrar y volver a abrir el panel del asistente CRM mantiene el hilo visible durante la sesión actual.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Las conversaciones del agente siguen en memoria del proceso y no sobreviven a un reinicio; su persistencia requiere una decisión de privacidad y retención.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
