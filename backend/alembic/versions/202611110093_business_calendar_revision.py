"""Use the configured business calendar for receivable and cash dates.

Revision ID: 202611110093
Revises: 202611100092
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110093"
down_revision = "202611100092"
branch_labels = None
depends_on = None

ITERATION = "Iteración 81 · calendario local de cobranza y caja · 2026-11-11"
CRITERIA = [
    "Las cuotas próximas, vencidas y de hoy se clasifican por la fecha del calendario de negocio, no por la fecha UTC del contenedor.",
    "Los avisos manuales de WhatsApp muestran la misma clasificación de fecha que la agenda de cobranza.",
    "Los vencimientos de clientes y proveedores se calculan sumando días calendario a una fecha ISO, sin convertirla a otra zona horaria.",
    "Los formularios de gastos, caja, compras y cobranza parten de la misma fecha del calendario de negocio que usa el CRM.",
]
QUESTIONS = [
    "ArcoEnergy debe confirmar la zona horaria oficial del negocio; DEV usa America/Cancun, coherente con el calendario que ya empleaba el CRM.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id in ("US-11", "US-16", "US-17", "US-18", "US-31", "US-34"):
        original = bind.execute(
            sa.select(history)
            .where(history.c.story_id == story_id)
            .order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
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
