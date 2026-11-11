"""Record cost-control and preliminary profitability coverage for US-12/38.

Revision ID: 202611110117
Revises: 202611110116
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110117"
down_revision = "202611110116"
branch_labels = None
depends_on = None

ITERATION = "Iteración 105 · costos directos y resultado preliminar · 2026-11-11"
REVISIONS = {
    "US-12": {
        "acceptance_criteria": [
            "El costo directo por orden/proyecto se calcula desde materiales consumidos confirmados y su costo unitario registrado; las devoluciones reutilizables disminuyen ese consumo.",
            "Si un movimiento no tiene costo conocido, el reporte señala la cantidad pendiente y no inventa un total de costo o resultado.",
        ],
        "unresolved_questions": [
            "El contador debe aprobar el método de valuación y tratamiento de ajustes antes de usar los importes como política contable oficial.",
        ],
    },
    "US-38": {
        "acceptance_criteria": [
            "El CRM ofrece saldos/flujo de efectivo, cartera por cobrar, valor y movimientos de almacén, y gastos por periodo/proyecto.",
            "El resultado preliminar por mes o proyecto usa ventas registradas menos costo de materiales y gastos, más devoluciones/bonificaciones aprobadas registradas.",
            "El informe identifica movimientos sin costo y se etiqueta como preliminar; no se presenta como estado financiero completo.",
        ],
        "unresolved_questions": [
            "Contabilidad debe definir fecha base, periodo/cierre, tratamiento fiscal y reclasificaciones antes de aprobar fórmulas como estados de resultados oficiales.",
        ],
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, additions in REVISIONS.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *additions["acceptance_criteria"]],
            "unresolved_questions": [*original["unresolved_questions"], *additions["unresolved_questions"]],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
