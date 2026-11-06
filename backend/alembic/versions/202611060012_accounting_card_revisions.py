"""Append each accounting implementation iteration to its source-backed cards.

Revision ID: 202611060012
Revises: 202611060011
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060012"
down_revision = "202611060011"
branch_labels = None
depends_on = None


IMPLEMENTATION_ITERATIONS = [
    (
        "Iteración 3 · compras y proveedores · 2026-11-06",
        {
            "US-18": ("Saldos de caja/banco reflejan pagos de compra ligados al proveedor. Pendiente: ventas, cobranza y conciliación bancaria.", ["US-21", "US-30", "US-31", "US-34"]),
            "US-21": ("Compra multirenglón con proveedor, referencia/factura, folio, costo por línea y entrada de existencias disponible. Pendiente: XML/OCR, impuestos/fletes y valoración acordada.", ["US-20", "US-30", "US-31", "US-34"]),
            "US-30": ("El saldo por pagar se deriva de compras y pagos vinculados al proveedor.", ["US-21", "US-31"]),
            "US-31": ("Anticipos y pagos parciales/totales reducen la cuenta por pagar y descuentan caja/banco. Pendiente: conciliación y reversa enlazada a la compra.", ["US-18", "US-21", "US-30", "US-34"]),
            "US-34": ("Pagos de compra ligados al proveedor se reflejan en las cuentas y conservan historial. Pendiente: ventas, cobranza y gastos.", ["US-18", "US-21", "US-30", "US-31"]),
        },
    ),
    (
        "Iteración 4 · gastos y cuentas · 2026-11-06",
        {
            "US-17": ("Gastos administrativos/contables requieren cuenta activa y generan salida de caja/banco; gastos de campo siguen registrándose por orden en PWA. Pendiente: autorización, conciliación y anticipos/reembolsos de campo.", ["US-10", "US-18", "US-34"]),
            "US-18": ("Gastos administrativos y pagos a proveedores afectan la cuenta elegida. Pendiente: ventas, cobranza y conciliación bancaria.", ["US-17", "US-21", "US-31", "US-34"]),
            "US-34": ("Movimientos ligados a compras y gastos administrativos se reflejan en cuentas con historial. Pendiente: enlazar ventas/cobros y conciliación.", ["US-17", "US-18", "US-21", "US-31"]),
        },
    ),
    (
        "Iteración 5 · cobranza de clientes · 2026-11-06",
        {
            "US-11": ("CRM permite registrar cuotas, abonos parciales y recordatorios WhatsApp iniciados por el encargado; los pagos aumentan la cuenta seleccionada. Pendiente: agenda y avisos automáticos y conexión con planes de venta.", ["US-16", "US-18", "US-34"]),
            "US-16": ("Cuotas manuales por cliente, forma de pago, pagos parciales con fecha/referencia e historial enlazado a caja/banco. Pendiente: generar cuotas desde ventas/crédito y distribuir un pago entre deudas.", ["US-11", "US-18", "US-34"]),
            "US-18": ("La cobranza aumenta caja/banco y los pagos ligados a compras/gastos reducen saldos. Pendiente: enlazar ventas, conciliación bancaria y externa.", ["US-11", "US-16", "US-17", "US-21", "US-31", "US-34"]),
            "US-34": ("Movimientos ligados a compras, gastos administrativos y abonos de clientes se reflejan en cuentas con historial. Pendiente: enlazar ventas y conciliación.", ["US-11", "US-16", "US-17", "US-18", "US-21", "US-31"]),
        },
    ),
]


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    rows = bind.execute(sa.select(table)).mappings().all()
    latest = {}
    for row in rows:
        if row["story_id"] not in latest or row["version"] > latest[row["story_id"]]["version"]:
            latest[row["story_id"]] = row

    now = datetime.now(timezone.utc)
    revisions = []
    for iteration, updates in IMPLEMENTATION_ITERATIONS:
        for story_id, (note, links) in updates.items():
            original = latest.get(story_id)
            if original is None:
                continue
            revision_row = dict(original)
            revision_row.update({
                "id": str(uuid4()),
                "version": original["version"] + 1,
                "iteration": iteration,
                # The stakeholder's source literal and provenance remain unchanged.
                "acceptance_criteria": [*original["acceptance_criteria"], f"Nota de implementación del equipo, no validada por el stakeholder: {note}"],
                "unresolved_questions": [*original["unresolved_questions"], "Validar efectos y reglas contables con Mario antes de tratar el sistema como libro contable."],
                "linked_cards": sorted(set([*original["linked_cards"], *links])),
                "recorded_by": "system:implementation-iteration",
                "created_at": now,
            })
            revisions.append(revision_row)
            latest[story_id] = revision_row
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    iteration_names = [iteration for iteration, _ in IMPLEMENTATION_ITERATIONS]
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration.in_(iteration_names), table.c.recorded_by == "system:implementation-iteration"))
