"""Record paired cash and bank transfer support.

Revision ID: 202611070056
Revises: 202611070055
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070056"
down_revision = "202611070055"
branch_labels = None
depends_on = None

ITERATION = "Iteración 45 · transferencias entre cuentas · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-18": (
            ["Una transferencia interna registra en una sola operación la salida de la cuenta origen y la entrada por el mismo importe a la cuenta destino."],
            ["La transferencia no incluye comisiones bancarias ni conciliación con estados de cuenta."],
        ),
        "US-19": (
            ["El flujo por cuenta clasifica las transferencias como movimientos compensados entre cuentas, sin contarlas como ingreso o gasto del negocio."],
            ["La conciliación y las comisiones siguen fuera del cálculo."],
        ),
        "US-35": (
            ["Las transferencias generan dos movimientos auditables con un identificador compartido y pueden revertirse en ambos lados de forma atómica."],
            ["No se crea póliza de doble partida ni se concilian saldos con bancos externos."],
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
