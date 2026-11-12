"""Record DEV deployment verification for the US-13 snapshot schedule.

Revision ID: 202611120137
Revises: 202611110136
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611120137"
down_revision = "202611110136"
branch_labels = None
depends_on = None

ITERATION = "Iteración 125 · verificación de despliegue DEV del respaldo · 2026-11-12"


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
            "Factory desplegó los recursos de ArcoEnergy DEV y verificó en vivo el esquema 202611110136.",
            "La configuración de Drive continúa pendiente; el estado idle no se registra como un respaldo ejecutado ni como archivo confirmado.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Verificar una carga real al autorizar carpeta privada de Drive y credenciales de cuenta de servicio.",
            "Acordar retención y procedimiento probado de restauración antes de considerar completa la protección de datos.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
