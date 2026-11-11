"""Record the append-only manual inventory receipt correction iteration.

Revision ID: 202611110122
Revises: 202611110121
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110122"
down_revision = "202611110121"
branch_labels = None
depends_on = None

ITERATION = "Iteración 110 · corrección de entradas manuales de inventario · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-36").order_by(history.c.version.desc())
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
            "Una entrada manual de inventario elegible se corrige con un movimiento compensatorio enlazado y un motivo obligatorio; el movimiento original permanece en el kardex.",
            "Compras, existencias iniciales, entradas con actividad posterior y correcciones que excedan el stock actual requieren conciliación desde su origen.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Las conciliaciones complejas de inventario deben validarse con Contabilidad antes de habilitar reversas de costo promedio o de entradas con actividad posterior.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
