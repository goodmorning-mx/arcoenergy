"""Record production access and no-trial verification in the source cards.

Revision ID: 202611060034
Revises: 202611060033
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060034"
down_revision = "202611060033"
branch_labels = None
depends_on = None

ITERATION = "Iteración 23 · salida de prueba y accesos reales · 2026-11-07"
UPDATES = {
    "US-14": "DEV confirma /crm/login, /app/login y el alias /login, con rutas privadas protegidas. Cinco roles están disponibles; no se crean ni afirman usuarios reales sin sus datos. La matriz de permisos por entidad/campo y pruebas con usuarios reales sigue pendiente.",
    "US-39": "DEV no muestra modo trial, contador, credenciales demo ni datos empresariales semilla. Los servicios API, CRM y PWA quedaron desplegados en d9fe896ade6e5a463d2ecfd4a62d7fc9c5029821. Faltan datos comerciales reales aprobados y configurar integraciones externas pendientes.",
    "US-40": "La PWA requiere autenticación y entrega la pantalla /app/login cuando no hay sesión. La ruta se verificó en DEV; faltan pruebas de acceso y operación con instaladores reales.",
}


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    rows = bind.execute(
        sa.select(table)
        .where(table.c.story_id.in_(UPDATES))
        .order_by(table.c.story_id, table.c.version.desc())
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
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [
                *original["acceptance_criteria"],
                f"Nota del equipo basada en verificación de DEV, no aprobación del stakeholder: {note}",
            ],
            "unresolved_questions": [
                *original["unresolved_questions"],
                "Solicitar datos de contacto y correo de cada empleado/cliente para crear y verificar sus cuentas reales.",
            ],
            "linked_cards": sorted(set([*original["linked_cards"], "US-14", "US-39", "US-40"])),
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        revisions.append(revised)
    if revisions:
        op.bulk_insert(table, revisions)


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
