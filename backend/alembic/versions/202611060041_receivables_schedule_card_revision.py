"""Record receivables agenda and contextual WhatsApp reminders.

Revision ID: 202611060041
Revises: 202611060040
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060041"
down_revision = "202611060040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-11").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 30 · agenda de cobranza y recordatorios contextuales · 2026-11-06",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "CRM filtra la agenda por vencidas, hoy, próximos siete días y pagadas; el encargado abre WhatsApp con un texto que incluye cuota, saldo, fecha o atraso y forma de pago.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Las cuotas de un plan de financiamiento se siguen registrando manualmente según fechas e importes acordados; generación automática del calendario y envío automático de mensajes siguen pendientes de definición/configuración.",
        ],
        "linked_cards": sorted(set([*original["linked_cards"], "US-16"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 30 · agenda de cobranza y recordatorios contextuales · 2026-11-06",
        history.c.recorded_by == "system:implementation-iteration",
    ))
