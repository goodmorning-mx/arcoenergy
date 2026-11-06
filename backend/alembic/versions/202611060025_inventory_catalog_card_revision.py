"""Append inventory metadata catalog implementation to its story card.

Revision ID: 202611060025
Revises: 202611060024
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060025"
down_revision = "202611060024"
branch_labels = None
depends_on = None

ITERATION = "Iteración 13 · datos identificables de inventario · 2026-11-06"
STORY_ID = "US-20"
NOTE = "El artículo de inventario registra descripción, categoría, marca, modelo, proveedor habitual y un identificador único opcional para QR/barras."


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    rows = bind.execute(sa.select(table).where(table.c.story_id == STORY_ID)).mappings().all()
    original = max(rows, key=lambda row: row["version"], default=None)
    if original is None:
        return
    revision_row = dict(original)
    revision_row.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"], f"Nota de implementación del equipo, no validada por el stakeholder: {NOTE}"],
        "unresolved_questions": [*original["unresolved_questions"], "Definir unidades/conversiones y generar/leer QR o códigos de barras por cámara."],
        "linked_cards": sorted(set([*original["linked_cards"], STORY_ID, "US-28"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [revision_row])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
