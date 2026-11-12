"""Record history-card search and related-card visibility for US-42.

Revision ID: 202611120141
Revises: 202611120140
"""
from datetime import datetime, timezone
from uuid import uuid4
from alembic import op
import sqlalchemy as sa

revision = "202611120141"
down_revision = "202611120140"
branch_labels = None
depends_on = None
ITERATION = "Iteración 129 · búsqueda y vínculos del historial de tarjetas · 2026-11-12"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-42").order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "La vista de history cards permite buscar entre versiones por ID, fuente literal, historia normalizada, stakeholder e iteración.",
            "Cada versión distingue vínculos a otras tarjetas de las relaciones entre la tarjeta y su fuente.",
        ],
        "unresolved_questions": [*original["unresolved_questions"]],
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
