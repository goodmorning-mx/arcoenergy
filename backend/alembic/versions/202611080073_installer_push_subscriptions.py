"""Store opt-in Web Push subscriptions for installer assignment alerts.

Revision ID: 202611080073
Revises: 202611080072
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080073"
down_revision = "202611080072"
branch_labels = None
depends_on = None

ITERATION = "Iteración 61 · avisos push de asignación a instaladores · 2026-11-08"

REVISIONS = {
    "US-7": (
        [
            "El instalador puede aceptar o desactivar avisos Web Push en su PWA; la suscripción queda vinculada a su propia cuenta y puede usarse en varios dispositivos.",
            "Al crear una orden asignada o registrar una venta que genera orden, el servidor envía un aviso aun con la PWA cerrada a las suscripciones de las personas asignadas; el aviso solo expone el folio y abre /app/.",
            "El instalador solo puede registrar o eliminar sus propias suscripciones; los endpoints push se restringen a servicios reconocidos por HTTPS.",
        ],
        [
            "Validar recepción y desactivación en dispositivos reales de cada instalador; la entrega final depende del sistema operativo, navegador y permisos de notificación.",
        ],
    ),
    "US-40": (
        [
            "La PWA registra una suscripción Web Push opcional en el servidor y su service worker muestra avisos de asignación cuando la interfaz no está abierta.",
        ],
        [
            "Validar instalación como PWA y recepción en segundo plano en Android/iOS usados por el equipo de campo.",
        ],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_push_subscriptions"):
        op.create_table(
            "ae_push_subscriptions",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("installer_email", sa.String(length=180), nullable=False),
            sa.Column("endpoint", sa.Text(), nullable=False),
            sa.Column("p256dh", sa.String(length=200), nullable=False),
            sa.Column("auth", sa.String(length=100), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("endpoint", name="uq_ae_push_subscriptions_endpoint"),
        )
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("ae_push_subscriptions")}
    indexes = {index["name"] for index in inspector.get_indexes("ae_push_subscriptions")}
    # The initial domain revision creates tables from current ORM metadata. On
    # a fresh database that means this table may already use the newer
    # user_email column, before this historical installer_email revision runs.
    if "installer_email" in columns and "ix_ae_push_subscriptions_installer_email" not in indexes:
        op.create_index("ix_ae_push_subscriptions_installer_email", "ae_push_subscriptions", ["installer_email"])
    elif "user_email" in columns and "ix_ae_push_subscriptions_user_email" not in indexes:
        op.create_index("ix_ae_push_subscriptions_user_email", "ae_push_subscriptions", ["user_email"])

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
