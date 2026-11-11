"""Record project-filtered cost and profitability reporting.

Revision ID: 202611100092
Revises: 202611100091
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100092"
down_revision = "202611100091"
branch_labels = None
depends_on = None

ITERATION = "Iteración 80 · consulta de costos por proyecto · 2026-11-10"
CRITERIA = [
    "El CRM permite filtrar el resultado operativo preliminar por mes y por proyecto.",
    "El filtro agrupa ventas, consumos, gastos y devoluciones/bonificaciones de todas las órdenes enlazadas al proyecto.",
    "La agenda de devoluciones/bonificaciones respeta el mismo periodo y proyecto seleccionado.",
    "El reporte conserva su base visible: ventas por registro, material por consumo confirmado y gastos por fecha capturada; no se presenta como estado financiero formal.",
]
QUESTIONS = [
    "El contador debe validar método de valuación, fechas contables, tratamiento de impuestos y alcance formal del estado de resultados.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id in ("US-12", "US-38"):
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
