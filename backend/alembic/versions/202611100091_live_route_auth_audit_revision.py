"""Record live route and anonymous API audit in story cards.

Revision ID: 202611100091
Revises: 202611100090
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100091"
down_revision = "202611100090"
branch_labels = None
depends_on = None

ITERATION = "Iteración 79 · auditoría viva de rutas y acceso · 2026-11-10"
CRITERIA = [
    "En DEV, las rutas /, /login, /crm/login, /app/login, /crm/ y /app/ sirven el portal correspondiente.",
    "Las colecciones privadas de clientes, cotizaciones, instalaciones y portal de cliente rechazan solicitudes anónimas.",
    "Solo la recepción pública de prospectos con consentimiento y el chat público del agente son rutas anónimas de producto.",
    "Los bundles publicados del CRM y la PWA no presentan cadenas de modo trial/demo.",
]
QUESTIONS = [
    "Validar inicio/cierre de sesión, redirección y permisos en navegador con cuentas reales de los cinco roles; no se crearán cuentas ficticias.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id in ("US-14", "US-39", "US-40"):
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
