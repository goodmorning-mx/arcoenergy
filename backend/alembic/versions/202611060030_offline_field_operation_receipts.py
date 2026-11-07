"""Add idempotent receipts for offline field operations and append card revisions.

Revision ID: 202611060030
Revises: 202611060029
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from app.models import OfflineOperation


revision = "202611060030"
down_revision = "202611060029"
branch_labels = None
depends_on = None

ITERATION = "Iteración 20 · sincronización segura de operaciones de campo · 2026-11-07"
UPDATES = {
    "US-9": "La PWA conserva consumos, devoluciones y gastos capturados sin conexión en una cola local por usuario. Al sincronizar, conserva el identificador hasta recibir confirmación del servidor. Pendiente validar el flujo operativo con instaladores.",
    "US-10": "Cada consumo, devolución o merma sincronizada conserva un identificador idempotente y su comprobante de resultado para evitar duplicados si se pierde la respuesta HTTP. Pendiente acordar con almacén la resolución de conflictos de existencias.",
    "US-40": "Los gastos de campo se pueden guardar en la cola local sin conexión y al reintentar no duplican el gasto ni su movimiento de caja. Pendiente definir evidencia y autorización de gastos por rol.",
}


def upgrade() -> None:
    # Initial schema revisions create tables from current ORM metadata. This
    # guarded metadata step adds the receipt table to older DEV databases and
    # is a no-op when it already exists in a fresh database.
    OfflineOperation.__table__.metadata.create_all(bind=op.get_bind(), tables=[OfflineOperation.__table__], checkfirst=True)

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
            "unresolved_questions": [*original["unresolved_questions"], "Definir el protocolo de resolución de conflictos y autorización de gastos con los stakeholders de campo."],
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
    # Preserve schema created by the initial metadata migration on downgrade.
