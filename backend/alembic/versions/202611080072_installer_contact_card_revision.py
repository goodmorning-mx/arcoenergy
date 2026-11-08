"""Record scoped installer contact details in source cards.

Revision ID: 202611080072
Revises: 202611080071
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080072"
down_revision = "202611080071"
branch_labels = None
depends_on = None

ITERATION = "Iteración 60 · contacto del cliente para órdenes asignadas · 2026-11-08"

REVISIONS = {
    "US-7": (
        [
            "La PWA muestra al instalador asignado el domicilio, teléfono y correo del cliente en la orden de trabajo, con acciones móviles para llamar y redactar un correo.",
            "El endpoint de instalaciones filtra las órdenes del rol instalador por asignación y devuelve para el contacto únicamente nombre, ciudad, domicilio, teléfono y correo, sin estado ni procedencia CRM.",
        ],
        [
            "La notificación cuando la PWA está cerrada requiere acordar/configurar un canal push o mensajería autorizado; la vista inmediata depende de que la app esté abierta.",
            "Falta validar con instaladores reales qué datos de contacto deben mostrarse y probarlos en sus teléfonos.",
        ],
    ),
    "US-14": (
        [
            "El acceso del instalador a instalaciones continúa limitado a sus órdenes asignadas y el resumen de cliente en esas órdenes expone solo los datos necesarios para coordinar la visita.",
        ],
        [
            "La matriz completa por entidad y campo sigue pendiente de validación con responsables y cuentas reales de cada rol.",
        ],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
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
