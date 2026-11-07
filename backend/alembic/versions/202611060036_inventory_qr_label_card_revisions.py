"""Record printable inventory QR labels and mobile lookup support.

Revision ID: 202611060036
Revises: 202611060035
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060036"
down_revision = "202611060035"
branch_labels = None
depends_on = None

ITERATION = "Iteración 25 · etiquetas QR de inventario · 2026-11-07"
UPDATES = {
    "US-20": "El CRM genera una etiqueta QR imprimible para cada artículo. Usa el barcode registrado cuando existe y un identificador interno AE-{id} cuando falta, sin escribir datos de prueba en inventario.",
    "US-28": "El escáner PWA puede resolver tanto el barcode definido en catálogo como el identificador interno codificado en la etiqueta QR generada. La operación requiere caché/inventario consultado y capacidades de cámara del dispositivo.",
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
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], f"Nota del equipo, no validada en dispositivos del stakeholder: {note}"],
            "unresolved_questions": [*original["unresolved_questions"], "Confirmar tamaño/material de impresión, formatos aceptados y compatibilidad de lector/cámara en los dispositivos de ArcoEnergy."],
            "linked_cards": sorted(set([*original["linked_cards"], "US-20", "US-28"])),
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        revisions.append(revised)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
