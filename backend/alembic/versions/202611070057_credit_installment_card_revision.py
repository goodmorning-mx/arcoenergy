"""Record credit sale installment scheduling support.

Revision ID: 202611070057
Revises: 202611070056
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070057"
down_revision = "202611070056"
branch_labels = None
depends_on = None

ITERATION = "Iteración 46 · calendario de cuotas de venta financiada · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-11": (
            ["Al registrar una venta a crédito, administración puede generar de 1 a 60 vencimientos semanales, quincenales o mensuales desde una fecha inicial; el monto aprobado se distribuye en cuotas y cualquier residuo de centavos queda en la última."],
            ["El calendario no calcula intereses ni comisiones; reglas de financiamiento, incluyendo Plan 24, requieren validación del contador."],
        ),
        "US-16": (
            ["Cada cuota de una venta financiada se registra como cuenta por cobrar individual con número, monto, método de pago y fecha de vencimiento para seguimiento y captura de pagos."],
            ["No se envían avisos automáticamente; los mensajes siguen siendo una acción manual de click-to-chat."],
        ),
    }
    for story_id, (criteria, questions) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
