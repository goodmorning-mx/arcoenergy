"""Append installation progress and portal access implementation notes.

Revision ID: 202611060020
Revises: 202611060019
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060020"
down_revision = "202611060019"
branch_labels = None
depends_on = None

ITERATION = "Iteración 9 · acceso de producto y avance de órdenes · 2026-11-06"
UPDATES = {
    "US-7": "El instalador recibe aviso local mientras la PWA está abierta, puede consultar su orden y actualizar su checklist; cada cambio se refleja en bitácora. Push de fondo queda pendiente de servicio y credenciales.",
    "US-14": "Las rutas /crm/login y /app/login separan los accesos y la cuenta cliente se dirige al portal PWA. La matriz de permisos por entidad/campo sigue pendiente.",
    "US-39": "CRM y PWA no muestran datos de muestra y exigen sesión para sus áreas internas. Los paquetes reales deben cargarse y aprobarse antes de cotizar.",
    "US-40": "La PWA guarda el avance del checklist en API, limita cambios al instalador asignado y enlaza notificaciones locales con la orden. No opera notificaciones push cuando la app está cerrada ni modo offline para acciones.",
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
            "unresolved_questions": [*original["unresolved_questions"], "Acordar servicio de notificaciones de fondo y definir si el avance de orden requiere evidencia/firma de supervisor."],
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
