"""Record reasoned, source-aware cash correction behavior.

Revision ID: 202611070059
Revises: 202611070058
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070059"
down_revision = "202611070058"
branch_labels = None
depends_on = None

ITERATION = "Iteración 48 · correcciones de caja con motivo y origen protegido · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-36": (
            ["Las correcciones de movimientos manuales de caja/banco exigen motivo y agregan una reversa enlazada sin borrar el original; las transferencias se corrigen en sus dos cuentas de forma atómica."],
            ["Las compras, ventas, gastos y pagos relacionados requieren flujos de corrección específicos para actualizar todos sus efectos."],
        ),
        "US-18": (
            ["Caja/bancos solo permite revertir movimientos manuales o transferencias desde la vista general; otros movimientos relacionados se corrigen desde su operación de origen."],
            ["La conciliación con estados de cuenta y comisiones bancarias continúa pendiente."],
        ),
        "US-35": (
            ["La reversa genérica rechaza movimientos enlazados con gastos, ventas u operaciones de pago para evitar que caja diverja del registro de origen."],
            ["Faltan flujos de reversa integral para ventas, gastos e inventario."],
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
