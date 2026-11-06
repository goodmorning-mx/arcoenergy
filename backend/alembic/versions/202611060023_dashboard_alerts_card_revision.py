"""Append permission-scoped operational dashboard alerts.

Revision ID: 202611060023
Revises: 202611060022
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060023"
down_revision = "202611060022"
branch_labels = None
depends_on = None

ITERATION = "Iteración 12 · alertas operativas del dashboard · 2026-11-06"
STORY_ID = "US-19"
NOTE = "El dashboard muestra artículos bajo mínimo, cuentas por cobrar vencidas o próximas a 7 días y saldos de caja/bancos, cada conjunto limitado a los permisos del usuario."


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
        "unresolved_questions": [*original["unresolved_questions"], "Definir umbrales/semáforos adicionales, periodo de caja, filtros y gráficas que administración y contador validarán como indicadores oficiales."],
        "linked_cards": sorted(set([*original["linked_cards"], STORY_ID, "US-11", "US-18", "US-26"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [revision_row])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
