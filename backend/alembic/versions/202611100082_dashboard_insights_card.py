"""Append the dashboard comparison and operational chart to US-37.

Revision ID: 202611100082
Revises: 202611100081
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100082"
down_revision = "202611100081"
branch_labels = None
depends_on = None

ITERATION = "Iteración 70 · dashboard con actividad y oportunidades operativas · 2026-11-10"
CRITERIA = [
    "El dashboard presenta el conteo diario de entradas y salidas físicas de almacén durante los últimos siete días, respetando los permisos de inventario.",
    "El dashboard resume artículos disponibles, bajo mínimo y sin existencia, y destaca acciones sobre stock, cobranza vencida y cotizaciones que esperan aprobación de precio.",
    "Los totales y las alertas del dashboard no revelan métricas de instalaciones, cotizaciones, inventario o cartera a roles que carecen del permiso correspondiente.",
]
QUESTIONS = [
    "Validar con contabilidad y administración las métricas prioritarias del dashboard y si desean comparativos por costo o valor de ventas una vez aprobadas sus reglas.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-37")
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
