"""Append the source-backed comparison of the existing CRM with US-37.

Revision ID: 202611060032
Revises: 202611060031
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060032"
down_revision = "202611060031"
branch_labels = None
depends_on = None

ITERATION = "Iteración 21 · comparación del sistema actual · 2026-11-07"
STORY_ID = "US-37"
NOTE = (
    "Se compararon las diez secciones del Word y PDF del contador con CRM/PWA en DEV. Hay cobertura básica "
    "de ventas/OT, cobranza, gastos, caja/bancos, inventario, compras/CxP, devoluciones, kardex y reportes. "
    "Pendientes principales: Plan 24, entidad/código de proyecto, cargar la orden externa, impuestos/pagos "
    "mixtos y validación de reportes. Ver docs/discovery/us-37-system-comparison.md."
)


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    original = op.get_bind().execute(
        sa.select(table).where(table.c.story_id == STORY_ID).order_by(table.c.version.desc()).limit(1)
    ).mappings().first()
    if original is None:
        return
    row = dict(original)
    row.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"], f"Nota del equipo, no validada por el stakeholder: {NOTE}"],
        "unresolved_questions": [*original["unresolved_questions"],
            "Definir Plan 24, el formato de proyecto, la política fiscal/reportes y el formato de orden externa con los stakeholders."],
        "linked_cards": sorted(set([*original["linked_cards"], "US-15", "US-21", "US-25", "US-32", "US-33", "US-38"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [row])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("story_id", sa.String()), sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.story_id == STORY_ID, table.c.iteration == ITERATION,
        table.c.recorded_by == "system:implementation-iteration"))
