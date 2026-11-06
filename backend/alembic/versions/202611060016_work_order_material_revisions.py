"""Append inventory reservation and installation consumption iteration.

Revision ID: 202611060016
Revises: 202611060015
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060016"
down_revision = "202611060015"
branch_labels = None
depends_on = None

ITERATION = "Iteración 7 · reserva y consumo de materiales · 2026-11-06"
UPDATES = {
    "US-7": "La PWA de instaladores presenta la orden asignada y los materiales solicitados, consumidos y pendientes.",
    "US-8": "La disponibilidad distingue existencia física de material reservado en órdenes abiertas.",
    "US-9": "La venta reserva materiales sin descontarlos; el consumo confirmado descuenta inventario una sola vez y queda ligado a la orden.",
    "US-12": "El inventario conserva cantidades físicas y calcula reservas abiertas para mostrar lo realmente disponible.",
    "US-15": "La creación de venta genera una solicitud de materiales ligada a la orden; no descuenta existencias físicas hasta confirmar entrega o consumo.",
    "US-20": "El catálogo de inventario expone existencia física, cantidad reservada y disponibilidad operativa.",
    "US-24": "La salida física se registra al confirmar consumo en campo; las líneas solicitadas y confirmadas quedan relacionadas con la orden.",
    "US-26": "El registro de consumo valida materiales y cantidades solicitadas en la orden y protege contra sobreconsumo.",
    "US-27": "El kardex distingue salidas físicas, consumo confirmado sin nueva salida y devoluciones relacionadas.",
    "US-29": "El inventario muestra cantidad disponible después de reservas por órdenes activas.",
    "US-32": "La orden foliada expone partidas de materiales solicitadas, confirmadas y pendientes.",
    "US-35": "Las reservas no alteran el saldo físico; los consumos, devoluciones y correcciones conservan trazabilidad para el costeo del proyecto.",
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
            "acceptance_criteria": [*original["acceptance_criteria"], f"Nota de implementación del equipo, no validada por el stakeholder: {note}"],
            "unresolved_questions": [*original["unresolved_questions"], "Validar con Mario el procedimiento físico de entrega/devolución, cantidades parciales y ajustes de materiales antes de cerrar la orden."],
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
