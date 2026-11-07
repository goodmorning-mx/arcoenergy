"""Track work-order assignment and confirmation for each installer.

Revision ID: 202611060038
Revises: 202611060037
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from app.models import InstallationAssignment


revision = "202611060038"
down_revision = "202611060037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    InstallationAssignment.__table__.create(bind=bind, checkfirst=True)
    installations = sa.table(
        "ae_installations",
        sa.column("id", sa.String()),
        sa.column("lead_installer", sa.String()),
    )
    assignments = sa.table(
        "ae_installation_assignments",
        sa.column("id", sa.String()),
        sa.column("installation_id", sa.String()),
        sa.column("installer_email", sa.String()),
        sa.column("assigned_by", sa.String()),
        sa.column("confirmed_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    rows = bind.execute(sa.select(installations.c.id, installations.c.lead_installer).where(installations.c.lead_installer != "")).all()
    now = datetime.now(timezone.utc)
    if rows:
        op.bulk_insert(assignments, [
            {"id": str(uuid4()), "installation_id": row.id, "installer_email": row.lead_installer.strip().lower(),
             "assigned_by": "migration:legacy-lead-installer", "confirmed_at": None, "created_at": now}
            for row in rows
        ])

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    updates = {
        "US-7": "La coordinación puede asignar una cuadrilla de varias cuentas activas de instalador; cada persona ve la orden, confirma su asignación y registra checklist, consumos, devoluciones y gastos dentro de sus permisos.",
        "US-40": "La PWA de cada instalador muestra órdenes asignadas a cualquiera de sus integrantes y permite confirmar individualmente la asignación. La sincronización requiere conexión; notificaciones push con la app cerrada siguen pendientes de proveedor.",
    }
    for story_id, note in updates.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1,
            "iteration": "Iteración 27 · asignación y confirmación de cuadrilla · 2026-11-07",
            "acceptance_criteria": [*original["acceptance_criteria"], f"Nota de implementación del equipo, pendiente de validación con instaladores: {note}"],
            "unresolved_questions": [*original["unresolved_questions"], "Validar flujo con instaladores reales y acordar el proveedor para notificaciones push en segundo plano."],
            "linked_cards": sorted(set([*original["linked_cards"], "US-7", "US-40"])),
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 27 · asignación y confirmación de cuadrilla · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
    InstallationAssignment.__table__.drop(bind=op.get_bind(), checkfirst=True)
