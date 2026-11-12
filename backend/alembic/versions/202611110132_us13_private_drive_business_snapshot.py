"""Append private business-data Drive snapshot support to US-13.

Revision ID: 202611110132
Revises: 202611110131
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110132"
down_revision = "202611110131"
branch_labels = None
depends_on = None

ITERATION = "Iteración 120 · exportación privada de datos a Drive · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-13").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return

    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Administración puede generar desde el CRM una exportación JSON privada de las tablas empresariales y perfiles/roles del equipo en Drive.",
            "La exportación omite hashes de contraseña, sesiones, claves/endpoints push y recibos técnicos de operaciones offline.",
            "La acción informa el resultado; no afirma guardado si Drive no está conectado o falla la carga.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta configurar y validar la carpeta privada y la cuenta de servicio de Drive en DEV.",
            "La exportación es manual; calendario automático, restauración y política de retención requieren configuración y revisión adicionales.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
