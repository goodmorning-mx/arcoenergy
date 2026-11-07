"""Record complete filtered kardex CSV export for US-27.

Revision ID: 202611060037
Revises: 202611060036
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060037"
down_revision = "202611060036"
branch_labels = None
depends_on = None

ITERATION = "Iteración 26 · exportación completa de kardex · 2026-11-07"
UPDATE = "La descarga CSV del CRM recorre todas las páginas filtradas de hasta 500 movimientos y exporta el conjunto completo. Se conserva el escape de fórmulas de hoja de cálculo y solo se agrega el costo unitario cuando el permiso lo autoriza."


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    original = bind.execute(
        sa.select(table).where(table.c.story_id == "US-27").order_by(table.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"], f"Nota del equipo, no validada por el stakeholder: {UPDATE}"],
        "unresolved_questions": [*original["unresolved_questions"], "Comprobar velocidad y memoria con el volumen real de movimientos y acordar el tamaño/formato de archivos extensos."],
        "linked_cards": sorted(set([*original["linked_cards"], "US-27"])),
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [revised])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
