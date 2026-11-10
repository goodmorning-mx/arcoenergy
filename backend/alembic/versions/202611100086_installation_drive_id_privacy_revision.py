"""Record private installation-document ID redaction in US-14.

Revision ID: 202611100086
Revises: 202611100085
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100086"
down_revision = "202611100085"
branch_labels = None
depends_on = None

ITERATION = "Iteración 74 · privacidad de documentos de instalación · 2026-11-10"
CRITERIA = [
    "Las respuestas de órdenes de trabajo no revelan identificadores privados de archivos de Drive; las interfaces reciben solo una señal de disponibilidad y descargan el archivo por una ruta autenticada con permisos.",
]
QUESTIONS = [
    "Probar la matriz de acceso completa con cuentas reales de administrador, contador, marketing, instalador y cliente.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-14")
        .order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
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
