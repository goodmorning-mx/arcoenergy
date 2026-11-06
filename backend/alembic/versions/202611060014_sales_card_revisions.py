"""Append sales and work-order implementation notes to linked story cards.

Revision ID: 202611060014
Revises: 202611060013
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060014"
down_revision = "202611060013"
branch_labels = None
depends_on = None


ITERATION = "Iteración 6 · ventas y órdenes · 2026-11-06"
UPDATES = {
    "US-7": ("Ventas aceptadas crean orden foliada y la asignan a un instalador activo; aparece en su PWA. Pendiente: notificaciones push/mensajería y confirmación de la cuadrilla.", ["US-15", "US-24", "US-32"]),
    "US-15": ("La cotización aceptada puede registrarse como venta de contado o crédito. Contado registra el ingreso en caja/banco; crédito crea un saldo por cobrar. Crea orden foliada y descuenta materiales del almacén. Pendiente: impuestos, pagos mixtos, plazos/abonos y reversas.", ["US-16", "US-18", "US-24", "US-32", "US-34", "US-35"]),
    "US-18": ("Ventas de contado aumentan caja/banco; abonos de venta a crédito aumentan la cuenta receptora; compras y gastos vinculados generan salidas. Pendiente: conciliación bancaria y libros contables.", ["US-15", "US-16", "US-17", "US-34", "US-35"]),
    "US-24": ("Materiales indicados al crear la orden se validan contra existencias, descuentan almacén y registran costo unitario en el kardex ligado al proyecto/instalación. Pendiente: distinguir solicitado, entregado, consumido y autorizado.", ["US-7", "US-15", "US-23", "US-27", "US-32"]),
    "US-32": ("Venta y orden de trabajo reciben folios únicos y quedan ligadas al cliente y cotización. Pendiente: entidad de proyecto independiente y formato de folio acordado con el stakeholder.", ["US-7", "US-15", "US-24"]),
    "US-34": ("Ingresos de ventas de contado y abonos de ventas a crédito se vinculan con caja/banco; las salidas de materiales quedan en el kardex ligado a la orden. Pendiente: conciliación y correcciones enlazadas.", ["US-15", "US-16", "US-18", "US-24", "US-35"]),
    "US-35": ("Venta desde cotización aceptada actualiza ingreso o cuenta por cobrar, salida de inventario por orden y folios relacionados en una transacción. No implementa todavía doble partida, impuestos, pagos mixtos ni reversa integral.", ["US-15", "US-16", "US-18", "US-24", "US-32", "US-34"]),
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
    for story_id, (note, links) in UPDATES.items():
        original = latest.get(story_id)
        if original is None:
            continue
        revision_row = dict(original)
        revision_row.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], f"Nota de implementación del equipo, no validada por el stakeholder: {note}"],
            "unresolved_questions": [*original["unresolved_questions"], "Validar con Mario el costeo, impuestos, pagos mixtos y reglas de reversa antes de contabilizar como estados financieros."],
            "linked_cards": sorted(set([*original["linked_cards"], *links])),
            "recorded_by": "system:implementation-iteration",
            "created_at": now,
        })
        revisions.append(revision_row)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
