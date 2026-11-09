"""Record order-specific material availability in discovery history.

Revision ID: 202611090077
Revises: 202611090076
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611090077"
down_revision = "202611090076"
branch_labels = None
depends_on = None

ITERATION = "Iteración 65 · disponibilidad de material por orden · 2026-11-09"
CRITERIA = [
    "Cada orden muestra la cantidad requerida pendiente de entregar, la existencia disponible para esa orden y el faltante calculado después de respetar las reservas de las demás órdenes abiertas.",
    "CRM y PWA presentan el faltante junto al proyecto al que corresponde; no repiten un déficit global como si perteneciera a cada orden.",
]
QUESTIONS = [
    "Validar en campo el cálculo con existencias y solicitudes reales, incluyendo devoluciones, órdenes cerradas y cambios concurrentes de almacén.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-8")
        .order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
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
