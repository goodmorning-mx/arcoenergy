"""Record paginated operational report behavior in source cards.

Revision ID: 202611080067
Revises: 202611080066
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080067"
down_revision = "202611080066"
branch_labels = None
depends_on = None

ITERATION = "Iteración 56 · reportes operativos paginados · 2026-11-08"

REVISIONS = {
    "US-27": (
        [
            "El kardex de reportes aplica el intervalo de fechas a todos los resultados y pagina de forma estable en bloques de hasta 500 movimientos.",
            "El CRM permite cargar los siguientes movimientos y comunica cuántos corresponden al intervalo seleccionado.",
            "La descarga CSV recorre todas las páginas del intervalo filtrado; los costos aparecen únicamente cuando la membresía tiene permiso para consultarlos.",
        ],
        ["Revisar rendimiento y comportamiento con el volumen histórico real del almacén."],
    ),
    "US-29": (
        [
            "El reporte operativo informa el total de movimientos del intervalo, pagina conjuntos mayores a 500 y permite recorrerlos desde CRM.",
            "La descarga CSV incluye todas las páginas del intervalo; la API mantiene el control de acceso a costos por permiso.",
        ],
        [
            "Validar con contabilidad los reportes de detalle y las fórmulas financieras; esta entrega cubre paginación/exportación del kardex, no un cierre contable.",
        ],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
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
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == ITERATION,
        history.c.recorded_by == "system:implementation-iteration",
    ))
