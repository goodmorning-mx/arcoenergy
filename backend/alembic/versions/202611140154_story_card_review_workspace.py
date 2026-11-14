"""Create append-only story-card review snapshots and stakeholder permissions.

Revision ID: 202611140154
Revises: 202611140153
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611140154"
down_revision = "202611140153"
branch_labels = None
depends_on = None

ITERATION = "Iteración 152 · espacio de revisión colaborativa de storycards · 2026-11-14"
ACCEPTANCE_CRITERION = (
    "El CRM muestra las storycards vigentes en una ruta de revisión con relato normalizado, fuente literal, criterios, preguntas abiertas, checklist y observaciones; "
    "cada guardado crea una revisión append-only ligada a la versión de la tarjeta y al usuario autenticado."
)
UNRESOLVED = (
    "La aceptación funcional queda disponible para revisión conjunta; los stakeholders aún deben marcar los criterios y registrar sus observaciones en el CRM."
)
REVIEW_ROLES = {"administrador", "contador", "marketing"}
REVIEW_PERMISSION = "history_cards:review"


def _append_history_card_revision(bind) -> None:
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    latest = bind.execute(
        sa.select(history).where(history.c.story_id == "US-42").order_by(history.c.version.desc())
    ).mappings().first()
    if latest is None:
        return
    acceptance = list(latest["acceptance_criteria"] or [])
    questions = list(latest["unresolved_questions"] or [])
    if ACCEPTANCE_CRITERION not in acceptance:
        acceptance.append(ACCEPTANCE_CRITERION)
    if UNRESOLVED not in questions:
        questions.append(UNRESOLVED)
    revised = dict(latest)
    revised.update({
        "id": str(uuid4()), "version": latest["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": acceptance, "unresolved_questions": questions,
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def _grant_review_permission(bind) -> None:
    if not sa.inspect(bind).has_table("gm_auth_memberships"):
        return
    memberships = sa.Table("gm_auth_memberships", sa.MetaData(), autoload_with=bind)
    rows = bind.execute(sa.select(
        memberships.c.user_id, memberships.c.organization_id,
        memberships.c.roles, memberships.c.permissions,
    )).mappings().all()
    for row in rows:
        roles = set(row["roles"] or [])
        if not roles.intersection(REVIEW_ROLES):
            continue
        permissions = list(row["permissions"] or [])
        if REVIEW_PERMISSION in permissions:
            continue
        permissions.append(REVIEW_PERMISSION)
        bind.execute(sa.update(memberships).where(
            memberships.c.user_id == row["user_id"],
            memberships.c.organization_id == row["organization_id"],
        ).values(permissions=permissions))


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("ae_history_cards") and not sa.inspect(bind).has_table("ae_history_card_reviews"):
        op.create_table(
            "ae_history_card_reviews",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("story_id", sa.String(length=30), nullable=False),
            sa.Column("history_card_id", sa.String(length=36), sa.ForeignKey("ae_history_cards.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("story_version", sa.Integer(), nullable=False),
            sa.Column("review_version", sa.Integer(), nullable=False),
            sa.Column("checklist", sa.JSON(), nullable=False),
            sa.Column("observations", sa.Text(), nullable=False),
            sa.Column("reviewed_by", sa.String(length=180), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("story_id", "review_version", name="uq_ae_history_card_review_version"),
        )
        op.create_index("ix_ae_history_card_reviews_story", "ae_history_card_reviews", ["story_id"])
        op.create_index("ix_ae_history_card_reviews_story_created", "ae_history_card_reviews", ["story_id", "created_at"])
    _grant_review_permission(bind)
    _append_history_card_revision(bind)


def downgrade() -> None:
    # Reviews and story history are append-only; rollback is forward-only.
    pass
