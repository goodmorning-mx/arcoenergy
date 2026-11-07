"""Record chart and detailed stock table coverage for US-19 and US-29.

Revision ID: 202611060033
Revises: 202611060032
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060033"
down_revision = "202611060032"
branch_labels = None
depends_on = None

ITERATION = "Iteración 22 · gráfico y detalle de disponibilidad · 2026-11-07"
UPDATES = {
    "US-19": "El dashboard/reportes añade lectura visual de artículos disponibles, con stock bajo y agotados. Sigue pendiente validar el flujo de efectivo, gráficas adicionales, indicadores y umbrales con administración y contador.",
    "US-29": "Reportes incluye un gráfico circular por estado de disponibilidad de artículos y una tabla detallada con existencia física, reservado, disponible, mínimo y categoría. El gráfico cuenta artículos en cada estado para no sumar unidades incompatibles. Pendientes otros reportes dedicados, paginación y validación contable.",
}


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    rows = bind.execute(sa.select(table).where(table.c.story_id.in_(UPDATES)).order_by(table.c.story_id, table.c.version.desc())).mappings().all()
    latest = {}
    for row in rows:
        latest.setdefault(row["story_id"], row)
    revisions = []
    for story_id, note in UPDATES.items():
        original = latest.get(story_id)
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], f"Nota del equipo, no validada por el stakeholder: {note}"],
            "unresolved_questions": [*original["unresolved_questions"], "Confirmar con administración si el resumen circular debe contar artículos, unidades homogéneas o valor monetario; el valor monetario requiere permiso de costos."],
            "linked_cards": sorted(set([*original["linked_cards"], "US-19", "US-29"])),
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        revisions.append(revised)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
