"""Record delivery of cash and bank accounts view for US-18.

Revision ID: 202611110111
Revises: 202611110110
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110111"
down_revision = "202611110110"
branch_labels = None
depends_on = None

ITERATION = "Iteración 99 · consulta de caja y bancos · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-18").order_by(history.c.version.desc())
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
            "El CRM muestra cuentas activas de efectivo/banco y sus saldos disponibles.",
            "Al elegir una cuenta, el usuario autorizado consulta su reporte de movimientos con fecha, origen, concepto e importe.",
            "Administración puede registrar cuentas y saldo inicial antes de capturar operaciones reales.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La conciliación contra estados bancarios queda fuera de esta tarjeta y requiere un flujo y reglas propios.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
