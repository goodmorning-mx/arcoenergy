"""Record anonymous runtime coverage for every private GET route in US-14.

Revision ID: 202611110096
Revises: 202611110095
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110096"
down_revision = "202611110095"
branch_labels = None
depends_on = None

ITERATION = "Iteración 84 · auditoría runtime de rutas privadas · 2026-11-11"
CRITERIA = [
    "Una prueba de integración consulta cada ruta GET privada del API sin sesión y exige una respuesta 401 o 403.",
    "La inspección de DEV recorrió las 34 rutas GET privadas publicadas por OpenAPI; todas devolvieron 401 sin datos.",
]
QUESTIONS = [
    "La autorización por rol y el aislamiento por organización/campo todavía deben validarse con cuentas reales de los cinco roles.",
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
