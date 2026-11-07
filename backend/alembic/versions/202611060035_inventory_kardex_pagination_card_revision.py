"""Record paginated inventory history in US-27.

Revision ID: 202611060035
Revises: 202611060034
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060035"
down_revision = "202611060034"
branch_labels = None
depends_on = None

ITERATION = "Iteración 24 · paginación de kardex · 2026-11-07"
UPDATE = "El API del kardex acepta páginas de hasta 500 movimientos con orden estable y el CRM permite cargar páginas consecutivas después de filtrar por artículo/fecha; CSV incluye todos los movimientos cargados. La PWA conserva el límite original para su consulta de campo."


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
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            f"Nota del equipo, no validada por el stakeholder: {UPDATE}",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar si los informes de auditoría requieren exportación de todas las páginas a un solo archivo y si deben conservar paginación para volúmenes superiores a los probados.",
        ],
        "linked_cards": sorted(set([*original["linked_cards"], "US-27"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [revised])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
