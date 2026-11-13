"""Record live PostgreSQL inventory verification for all 42 story cards.

Revision ID: 202611130146
Revises: 202611130145
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130146"
down_revision = "202611130145"
branch_labels = None
depends_on = None
ITERATION = "Iteración 144 · auditoría PostgreSQL de las 42 tarjetas · 2026-11-13"
CARD_UPDATE = (
    "La base PostgreSQL de DEV contiene 42 story cards distintas en ae_history_cards y 344 versiones append-only; las 344 filas conservan source_literal no vacío. "
    "La auditoría verificó también las versiones actuales US-9 v7, US-14 v34 y US-40 v24.",
    "Falta cotejo humano de transcripciones y reconstrucciones con sus stakeholders, y confirmar la política de retención de fuentes sensibles.",
)


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-42").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    criterion, unresolved = CARD_UPDATE
    revised = dict(original)
    acceptance = list(original["acceptance_criteria"] or [])
    questions = list(original["unresolved_questions"] or [])
    if criterion not in acceptance:
        acceptance.append(criterion)
    if unresolved not in questions:
        questions.append(unresolved)
    revised.update({
        "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": acceptance, "unresolved_questions": questions,
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
