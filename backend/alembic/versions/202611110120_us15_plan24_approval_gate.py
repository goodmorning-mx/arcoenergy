"""Record the Plan 24 business-rule gate for US-15.

Revision ID: 202611110120
Revises: 202611110119
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110120"
down_revision = "202611110119"
branch_labels = None
depends_on = None

ITERATION = "Iteración 108 · resguardo de ventas Plan 24 · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-15").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Una cotización marcada Plan 24 no se puede convertir en venta/crédito ordinario ni generar cartera hasta que contabilidad apruebe las reglas de la tanda.",
            "La propuesta Plan 24 permanece consultable y el CRM explica el bloqueo sin crear venta, orden, cuenta por cobrar ni movimiento de efectivo.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Contabilidad debe definir anticipo, calendario y distribución de pagos, incumplimiento, tratamiento de inventario y relación con las tandas antes de habilitar Plan 24.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
