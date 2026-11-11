"""Record fresh-schema compatibility for Web Push subscriptions.

Revision ID: 202611110094
Revises: 202611110093
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110094"
down_revision = "202611110093"
branch_labels = None
depends_on = None

ITERATION = "Iteración 82 · compatibilidad de esquema push · 2026-11-11"
REVISIONS = {
    "US-7": (
        ["La migración de suscripciones push funciona tanto con el esquema histórico installer_email como con el esquema user_email creado por la metadata vigente."],
        [],
    ),
    "US-40": (
        ["Una instalación limpia puede aplicar todas las migraciones de la PWA y CRM push desde cero sin detener el backend."],
        [],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
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
