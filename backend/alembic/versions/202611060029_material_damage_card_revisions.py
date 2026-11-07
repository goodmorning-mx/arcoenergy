"""Append linked work-order material damage revisions to history cards.

Revision ID: 202611060029
Revises: 202611060028
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060029"
down_revision = "202611060028"
branch_labels = None
depends_on = None

ITERATION = "Iteración 19 · devolución reutilizable y merma de obra · 2026-11-07"
UPDATES = {
    "US-23": "La devolución de una salida puede marcarse como sobrante reutilizable o pieza dañada. Solo el material reutilizable aumenta existencias; ambos estados quedan ligados a la salida original. Pendiente validar con almacén la aprobación de devoluciones y tratamiento de materiales reparables.",
    "US-24": "La merma de material en orden se registra sin reponer existencias y genera el evento de costo faltante cuando el material aún no se había confirmado como consumido. La corrección de consumo ya confirmado conserva su costo sin duplicarlo.",
    "US-27": "El kardex identifica la merma de material dañado con cambio físico cero porque la salida original ya descontó las piezas; conserva la relación con la salida y el costo de proyecto. Pendiente filtro/exportación específica de mermas.",
    "US-35": "Las mermas de material preemitido generan costo de consumo ligado a la orden; las mermas de material ya consumido no duplican el costo. Libros de doble partida y reglas contables siguen pendientes de validación.",
}


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    rows = bind.execute(
        sa.select(table).where(table.c.story_id.in_(UPDATES)).order_by(table.c.story_id, table.c.version.desc())
    ).mappings().all()
    latest = {}
    for row in rows:
        latest.setdefault(row["story_id"], row)
    revisions = []
    for story_id, note in UPDATES.items():
        original = latest.get(story_id)
        if original is None:
            continue
        revision_row = dict(original)
        revision_row.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], f"Nota del equipo, no validada por el stakeholder: {note}"],
            "unresolved_questions": [*original["unresolved_questions"], "Definir con el responsable de almacén el proceso de inspección, aprobación y destino de material dañado o reparable."],
            "linked_cards": sorted(set([*original["linked_cards"], *UPDATES.keys()])),
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        revisions.append(revision_row)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
