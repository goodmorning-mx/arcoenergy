"""Append the kardex filtering and CSV export card revision.

Revision ID: 202611060021
Revises: 202611060020
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060021"
down_revision = "202611060020"
branch_labels = None
depends_on = None

ITERATION = "Iteración 10 · exportación del kardex · 2026-11-06"
STORY_ID = "US-27"
NOTE = "CRM permite filtrar movimientos por artículo y rango de fechas y descargar el resultado visible como CSV; los costos solo se exportan con permiso de lectura de costos."


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
        "unresolved_questions": [*original["unresolved_questions"], "Acordar retención, separador/formato regional y volumen máximo que debe cubrir una exportación."],
        "linked_cards": sorted(set([*original["linked_cards"], STORY_ID])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [revision_row])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
