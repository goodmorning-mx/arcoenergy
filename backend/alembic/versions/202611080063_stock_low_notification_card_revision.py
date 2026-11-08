"""Record stock notification behavior for the inventory story card.

Revision ID: 202611080063
Revises: 202611080062
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080063"
down_revision = "202611080062"
branch_labels = None
depends_on = None

ITERATION = "Iteración 52 · avisos de stock bajo en PWA · 2026-11-08"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-26")
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"],
            "Con permiso de notificaciones, la PWA avisa cuando el inventario consultado cruza el mínimo configurado; resume artículos y evita repetir avisos mientras continúen bajo el mismo mínimo."],
        "unresolved_questions": [*original["unresolved_questions"],
            "Los avisos locales requieren que la PWA esté abierta y conectada para detectar cambios; falta acordar destinatarios centrales y notificaciones push con la aplicación cerrada."],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
