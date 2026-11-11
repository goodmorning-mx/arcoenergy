"""Record delivery of customer receivables collection criteria for US-16.

Revision ID: 202611110113
Revises: 202611110112
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110113"
down_revision = "202611110112"
branch_labels = None
depends_on = None

ITERATION = "Iteración 101 · cobranza de clientes y flujo de efectivo · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-16").order_by(history.c.version.desc())
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
            "CRM permite registrar abonos parciales o el pago completo con importe, fecha, cuenta de efectivo/banco y referencia opcional.",
            "Cada pago queda enlazado a la cuenta por cobrar, el cliente y el movimiento de caja; actualiza el saldo pendiente.",
            "Los movimientos recibidos aparecen en saldo y reporte de la cuenta seleccionada, con historial corregible mediante reversa trazable.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La aplicación automática de un pago a varias deudas/cuotas y el tratamiento de mora/cancelaciones requieren reglas del contador.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
