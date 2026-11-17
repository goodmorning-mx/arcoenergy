"""Record the implementation proposal for each story-card review.

Revision ID: 202611170157
Revises: 202611170156
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611170157"
down_revision = "202611170156"
branch_labels = None
depends_on = None

ITERATION = "Iteración 155 · solución propuesta por storycard · 2026-11-17"
SOURCE_LITERAL = "si me gusto la revision de storycards podrias poner el campo de solucion propuesta como que se agrego el campo o la pantalla etc para como resolvimos ese storycard"
ACCEPTANCE_CRITERIA = (
    "La tabla de revisión de storycards incluye una columna Solución propuesta que describe la pantalla, campo, flujo u otro cambio implementado para atender cada tarjeta.",
    "Cada solución propuesta se puede agregar o editar desde un modal y queda guardada en una revisión append-only con autor y fecha.",
    "Actualizar la solución propuesta conserva el estado Finished, el checklist y los comentarios; cambiar cualquiera de estos datos conserva la solución.",
)
UNRESOLVED = "La solución propuesta documenta el trabajo de implementación y no sustituye la confirmación del stakeholder ni el estado Finished."


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_card_reviews"):
        return
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_history_card_reviews")}
    if "solution_proposed" not in columns:
        op.add_column("ae_history_card_reviews", sa.Column("solution_proposed", sa.Text(), nullable=False, server_default=""))
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    cards = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    latest = bind.execute(sa.select(cards).where(cards.c.story_id == "US-42").order_by(cards.c.version.desc())).mappings().first()
    if latest is None:
        return
    criteria = list(latest["acceptance_criteria"] or [])
    questions = list(latest["unresolved_questions"] or [])
    for criterion in ACCEPTANCE_CRITERIA:
        if criterion not in criteria:
            criteria.append(criterion)
    if UNRESOLVED not in questions:
        questions.append(UNRESOLVED)
    revised = dict(latest)
    revised.update({
        "id": str(uuid4()), "version": latest["version"] + 1, "iteration": ITERATION,
        "source_literal": SOURCE_LITERAL, "source_type": "Solicitud en conversación",
        "source_reference": "Conversación del proyecto Arco Energy · 2026-11-17",
        "source_attribution": "Stakeholder Arco Energy (autor nominal por identificar)",
        "source_confidence": "verbatim", "source_language": "es",
        "acceptance_criteria": criteria, "unresolved_questions": questions,
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(cards.insert().values(**revised))


def downgrade() -> None:
    # Preserve append-only story and review history on rollback.
    pass
