"""Append preliminary project and monthly profitability report iteration.

Revision ID: 202611060019
Revises: 202611060018
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060019"
down_revision = "202611060018"
branch_labels = None
depends_on = None

ITERATION = "Iteración 8 · costeo preliminar por proyecto y mes · 2026-11-06"
UPDATES = {
    "US-15": "Ventas registradas alimentan el reporte mensual por fecha de registro; el reporte distingue venta de flujo de caja.",
    "US-17": "El reporte suma gastos por fecha capturada y proyecto opcional, con totales por categoría.",
    "US-24": "El costo de materiales usa eventos de consumo confirmado y devoluciones de consumo con costo unitario histórico; faltan autorizaciones y tratamiento fiscal.",
    "US-27": "El kardex conserva eventos de consumo para costearlos por fecha sin descontar existencias por segunda vez.",
    "US-32": "El reporte puede filtrarse por orden/proyecto y agruparse mensualmente.",
    "US-35": "El cálculo operativo preliminar enlaza ventas, costo de materiales y gastos; no es doble partida ni sustituye registros contables.",
    "US-38": "CRM presenta resultado preliminar por mes/proyecto como ventas menos costo de consumo confirmado y gastos; devoluciones de venta, bonificaciones, impuestos y cierres contables siguen fuera del cálculo.",
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
            "unresolved_questions": [*original["unresolved_questions"], "Acordar con Mario y Josué cómo reconocer temporalmente costos, devoluciones, bonificaciones e impuestos antes de tratar este resultado como estado financiero formal."],
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
