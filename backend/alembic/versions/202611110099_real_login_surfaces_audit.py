"""Record DEV verification of production-mode login surfaces.

Revision ID: 202611110099
Revises: 202611110098
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110099"
down_revision = "202611110098"
branch_labels = None
depends_on = None

ITERATION = "Iteración 87 · login real sin modo de prueba · 2026-11-11"
CRITERIA = [
    "La página pública de DEV y las rutas de acceso /login, /crm/login y /app/login responden correctamente; Chrome renderiza el formulario en cada ruta.",
    "Los bundles activos de PWA y CRM no contienen marcadores de modo trial/demo ni mensajes de prueba gratuita.",
    "Las rutas privadas no entregan datos sin sesión: la auditoría de la Iteración 86 verificó 35/35 lecturas con HTTP 401.",
]
QUESTIONS = [
    "No se crearon cuentas de personal ni de clientes: falta que ArcoEnergy indique los usuarios y correos reales que deben habilitarse; la configuración inicial de cuenta se gestiona por el administrador/bootstrap autorizado.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id in ("US-39", "US-40"):
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
            "acceptance_criteria": [*original["acceptance_criteria"], *CRITERIA],
            "unresolved_questions": [*original["unresolved_questions"], *QUESTIONS],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
