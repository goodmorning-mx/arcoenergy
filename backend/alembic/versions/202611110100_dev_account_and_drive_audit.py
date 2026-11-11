"""Record account and Drive configuration blockers found during DEV audit.

Revision ID: 202611110100
Revises: 202611110099
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110100"
down_revision = "202611110099"
branch_labels = None
depends_on = None

ITERATION = "Iteración 88 · auditoría de usuarios y Drive en DEV · 2026-11-11"
STORIES = {
    "US-13": (
        ["En el contenedor API activo de DEV no están configurados Google Drive folder ID ni credenciales de service account; la integración de Drive no puede operar en ese entorno."],
        ["ArcoEnergy debe autorizar y configurar una carpeta, sus permisos, retención y credenciales administradas antes de activar almacenamiento Drive en DEV."],
    ),
    "US-14": (
        ["La inspección agregada de membresías activas en DEV encontró una cuenta administrador y ninguna cuenta activa de contador, marketing, instalador o cliente; no se consultaron ni almacenaron identidades."],
        ["Validar el alcance efectivo con cuentas reales de los cinco roles cuando ArcoEnergy habilite las personas que faltan."],
    ),
    "US-39": (
        ["El acceso inicial de DEV tiene un administrador activo configurado; no se encontraron cuentas activas de personal en los otros roles."],
        ["ArcoEnergy debe proporcionar los correos de personal autorizados y validar su acceso autenticado."],
    ),
    "US-40": (
        ["La PWA está publicada, pero en DEV no hay cuentas activas de contador, marketing, instalador o cliente para completar el recorrido de campo."],
        ["Habilitar las cuentas autorizadas y probar permisos, sincronización y notificaciones en los teléfonos del equipo."],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in STORIES.items():
        original = bind.execute(
            sa.select(history)
            .where(history.c.story_id == story_id)
            .order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
