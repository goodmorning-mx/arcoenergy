"""Append order material cost privacy coverage to US-14.

Revision ID: 202611100084
Revises: 202611100083
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100084"
down_revision = "202611100083"
branch_labels = None
depends_on = None

ITERATION = "Iteración 72 · privacidad de costos en órdenes de trabajo · 2026-11-10"
CRITERIA = [
    "La lista de órdenes de trabajo no expone el costo unitario de sus materiales a instaladores; sigue mostrando cantidades y disponibilidad para operar.",
]
QUESTIONS = [
    "La validación integral por rol todavía requiere las cuentas reales de contador, marketing, instalador y cliente y su confirmación por los responsables.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-14")
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
