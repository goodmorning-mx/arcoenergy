"""Persist stakeholder completion state and record the table iteration.

Revision ID: 202611170156
Revises: 202611160155
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611170156"
down_revision = "202611160155"
branch_labels = None
depends_on = None

ITERATION = "Iteración 154 · tabla de revisión, estado y comentarios · 2026-11-17"
ACCEPTANCE_CRITERIA = (
    "La revisión CRM presenta en una tabla el número de storycard, el relato real conservado literalmente, la historia interpretada, el autor solicitante, el estado terminado y los comentarios.",
    "Cada tarjeta permite marcar Pendiente o Terminada con controles de radio; el estado queda persistido entre sesiones y ligado a la versión revisada.",
    "Los comentarios se agregan en un modal y se conservan como revisiones append-only con autor y fecha.",
    "Agregar una nueva historycard se realiza desde un modal que conserva el relato literal, la procedencia y la historia interpretada como campos separados.",
)
UNRESOLVED = "Confirmar con cada stakeholder el contenido interpretado y marcar Terminada únicamente después de su revisión; el estado técnico no equivale a aprobación de negocio."
SOURCE_LITERAL = "cambia la vista de UIUX de storycards necesito que pongas una tabla con num de storycard; con el storycard real con el storycard interpretado y con el autor y con el finished con un radio button y con comments que podemos agregar, el flujo de agregar otra historycard es un modal"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_card_reviews"):
        return
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_history_card_reviews")}
    if "finished" not in columns:
        op.add_column("ae_history_card_reviews", sa.Column("finished", sa.Boolean(), nullable=False, server_default=sa.false()))
    reviews = sa.Table("ae_history_card_reviews", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(sa.select(reviews.c.id, reviews.c.checklist)).mappings():
        checklist = row["checklist"] or []
        finished = bool(checklist) and all(item.get("checked", False) for item in checklist)
        bind.execute(sa.update(reviews).where(reviews.c.id == row["id"]).values(finished=finished))
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
    revised.update({"id": str(uuid4()), "version": latest["version"] + 1, "iteration": ITERATION,
                    "acceptance_criteria": criteria, "unresolved_questions": questions,
                    "source_literal": SOURCE_LITERAL, "source_type": "Solicitud en conversación",
                    "source_reference": "Conversación del proyecto Arco Energy · 2026-11-17",
                    "source_attribution": "Stakeholder Arco Energy (autor nominal por identificar)",
                    "source_confidence": "verbatim", "source_language": "es",
                    "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc)})
    bind.execute(cards.insert().values(**revised))


def downgrade() -> None:
    # Keep append-only history; the completion state remains available on rollback.
    pass
