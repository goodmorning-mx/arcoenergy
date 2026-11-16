"""Track the person who requested each history card and filter by author.

Revision ID: 202611160155
Revises: 202611140154
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611160155"
down_revision = "202611140154"
branch_labels = None
depends_on = None

ITERATION = "Iteración 153 · autor y filtro de solicitudes en history cards · 2026-11-16"
UNKNOWN_AUTHOR = "Por identificar"
GOITO_STORIES = {f"US-{number}" for number in range(1, 15)}
MARIO_STORIES = {*(f"US-{number}" for number in range(15, 33)), *(f"US-{number}" for number in range(35, 39))}
AUTHOR_BY_STORY_ID = {
    **{story_id: "Goito Profugo" for story_id in GOITO_STORIES},
    **{story_id: "Mario Groso" for story_id in MARIO_STORIES},
}
ACCEPTANCE_CRITERIA = (
    "Cada history card incluye un campo separado para la persona que solicitó el requerimiento; las atribuciones confirmadas se normalizan a Goito Profugo o Mario Groso, y las fuentes sin autor nominal permanecen como 'Por identificar'.",
    "La revisión CRM muestra el autor solicitante en la tabla y el detalle, y filtra tarjetas por persona sin cambiar la procedencia literal de la fuente.",
)
UNRESOLVED = (
    "La atribución nominal de las transcripciones ASR y de las solicitudes atribuidas al dueño del producto sigue pendiente de confirmación; no debe inferirse a partir de roles o cuentas administrativas.",
)


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_history_cards")}
    if "requested_by" not in columns:
        op.add_column(
            "ae_history_cards",
            sa.Column("requested_by", sa.String(length=180), nullable=False, server_default=UNKNOWN_AUTHOR),
        )

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    rows = bind.execute(sa.select(history.c.id, history.c.story_id)).mappings().all()
    for row in rows:
        author = AUTHOR_BY_STORY_ID.get(row["story_id"], UNKNOWN_AUTHOR)
        bind.execute(sa.update(history).where(history.c.id == row["id"]).values(requested_by=author))

    latest = bind.execute(
        sa.select(history).where(history.c.story_id == "US-42").order_by(history.c.version.desc())
    ).mappings().first()
    if latest is None:
        return
    acceptance = list(latest["acceptance_criteria"] or [])
    questions = list(latest["unresolved_questions"] or [])
    for criterion in ACCEPTANCE_CRITERIA:
        if criterion not in acceptance:
            acceptance.append(criterion)
    if UNRESOLVED not in questions:
        questions.append(UNRESOLVED)
    revised = dict(latest)
    revised.update({
        "id": str(uuid4()),
        "version": latest["version"] + 1,
        "iteration": ITERATION,
        "requested_by": AUTHOR_BY_STORY_ID.get("US-42", UNKNOWN_AUTHOR),
        "acceptance_criteria": acceptance,
        "unresolved_questions": questions,
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    # Keep author metadata and append-only story history on rollback.
    pass
