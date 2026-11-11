"""Record delivered operations reports for US-29.

Revision ID: 202611110108
Revises: 202611110107
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110108"
down_revision = "202611110107"
branch_labels = None
depends_on = None

ITERATION = "Iteración 96 · cobertura de reportes operativos · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-29").order_by(history.c.version.desc())
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
            "El CRM muestra existencias actuales en una gráfica de disponibilidad y una tabla por artículo.",
            "El reporte operativo permite consultar movimientos de almacén, clientes, proveedores, proyectos/órdenes por estado y gastos dentro del periodo.",
            "La API restringe los costos unitarios y el flujo de efectivo según los permisos del usuario; los totales descriptivos no se presentan como pólizas o estados financieros oficiales.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La selección de indicadores contables, costos históricos y fórmulas de resultado pertenece a US-12 y US-38 y requiere validación del contador.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
