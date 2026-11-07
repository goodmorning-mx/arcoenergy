"""Append offline field checklist support to US-40 history.

Revision ID: 202611060028
Revises: 202611060027
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060028"
down_revision = "202611060027"
branch_labels = None
depends_on = None

ITERATION = "Iteración 18 · checklist de campo sin conexión · 2026-11-07"
UPDATES = {
    "US-14": "DEV verifica inicio de sesión CRM/PWA con las rutas configuradas y la cuenta existente de administrador. No se considera verificada una cuenta operativa por cada rol; la matriz de permisos por campo sigue pendiente.",
    "US-39": "CRM y PWA en DEV responden en sus rutas de acceso y la API autentica la cuenta real existente como administrador. No se crean usuarios ficticios; falta provisionar y validar cuentas de instalador, contador, marketing y cliente con los responsables del negocio.",
    "US-40": (
    "La PWA de instaladores conserva localmente las órdenes previamente consultadas y permite "
    "poner cambios del checklist en cola cuando no hay conexión. Al reconectar, vuelve a consultar "
    "las órdenes autorizadas y sincroniza cambios idempotentes por tarea. Cerrar sesión borra la "
    "caché de órdenes de ese instalador. Consumos, devoluciones y gastos siguen requiriendo "
    "conexión; trabajo offline completo y notificaciones de fondo siguen pendientes."
    ),
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
            "unresolved_questions": [*original["unresolved_questions"], "Validar permisos por rol y uso de caché local/dispositivos de campo con ArcoEnergy; provisionar cuentas reales para los roles acordados."],
            "linked_cards": sorted(set([*original["linked_cards"], *UPDATES.keys(), "US-7", "US-9"])),
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        revisions.append(revision_row)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
