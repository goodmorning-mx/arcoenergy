"""Record the live anonymous read-route audit for US-14.

Revision ID: 202611110098
Revises: 202611110097
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110098"
down_revision = "202611110097"
branch_labels = None
depends_on = None

ITERATION = "Iteración 86 · auditoría de rutas privadas en DEV · 2026-11-11"
CRITERIA = [
    "El contrato OpenAPI publicado declara 35 rutas GET privadas y todas devuelven 401 cuando se solicitan sin sesión.",
    "DEV sirve PWA, CRM y acceso web; las rutas /app/login, /crm/login y /login renderizan el formulario en Chrome.",
    "La API y los manifiestos de versión PWA/CRM reportan commit dcf384f0ad8dc09f7b2007da14685c2be6672663 y esquema 202611110097.",
]
QUESTIONS = [
    "La auditoría confirma acceso anónimo denegado, pero no sustituye pruebas de alcance por entidad/campo ni validación del negocio con cuentas de cada rol.",
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
