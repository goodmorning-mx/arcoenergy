"""Append source-backed history-card revisions for linked payment corrections.

Revision ID: 202611060027
Revises: 202611060026
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060027"
down_revision = "202611060026"
branch_labels = None
depends_on = None

ITERATION = "Iteración 17 · correcciones enlazadas de pagos · 2026-11-07"
UPDATES = {
    "US-16": "Un abono de cliente se corrige mediante una nueva fila enlazada; el saldo por cobrar y el movimiento de caja/banco se revierten juntos y la operación original se conserva.",
    "US-18": "La corrección de un pago ligado actualiza en una sola operación el saldo de caja/banco y la deuda asociada; conciliación bancaria sigue pendiente.",
    "US-31": "Pagos a proveedores permiten corrección append-only con motivo, saldo por pagar y caja/banco actualizados juntos. La reversa de la compra completa y la conciliación siguen pendientes.",
    "US-34": "Pagos de clientes y proveedores enlazan reversas de caja/banco con el pago original y su saldo; no se borran filas. Otros tipos de operación y conciliación siguen pendientes.",
    "US-36": "Se corrigen abonos de clientes y pagos a proveedores agregando eventos vinculados que revierten sus efectos financieros. No se permite revertir manualmente el movimiento de caja de un pago enlazado.",
}


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    rows = bind.execute(sa.select(table).where(table.c.story_id.in_(UPDATES))).mappings().all()
    latest = {}
    for row in rows:
        if row["story_id"] not in latest or row["version"] > latest[row["story_id"]]["version"]:
            latest[row["story_id"]] = row
    now = datetime.now(timezone.utc)
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
            "unresolved_questions": [*original["unresolved_questions"], "Validar con Mario el procedimiento para reversas parciales, compras completas, devoluciones y conciliación bancaria."],
            "linked_cards": sorted(set([*original["linked_cards"], *UPDATES.keys()])),
            "recorded_by": "system:implementation-iteration",
            "created_at": now,
        })
        revisions.append(revision_row)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
