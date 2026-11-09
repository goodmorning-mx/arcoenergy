"""Deliver CRM follow-up reminders through the existing Web Push service.

Revision ID: 202611090076
Revises: 202611090075
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611090076"
down_revision = "202611090075"
branch_labels = None
depends_on = None

ITERATION = "Iteración 64 · recordatorios push de seguimiento · 2026-11-09"
REVISIONS = {
    "US-4": (
        [
            "La persona comercial puede activar Web Push desde CRM y recibe el aviso el día de vencimiento aunque cierre el CRM, si el dispositivo y navegador permiten notificaciones en segundo plano.",
            "El servidor consulta vencimientos pendientes, respeta la persona responsable, deduplica cada seguimiento y reintenta fallas transitorias o reclamos abandonados.",
            "El aviso push solo informa que hay un seguimiento pendiente y abre CRM; no incluye datos ni comentarios del cliente.",
        ],
        [
            "Validar la recepción y desactivación en los navegadores y teléfonos reales del equipo comercial.",
        ],
    ),
    "US-39": (
        [
            "El CRM reutiliza el service worker PWA y el canal Web Push administrado para recordar seguimientos aun cuando el CRM esté cerrado.",
        ],
        [
            "La entrega depende de permisos del navegador, conectividad y restricciones del sistema operativo; faltan pruebas con cuentas reales.",
        ],
    ),
    "US-40": (
        [
            "El service worker de la PWA recibe avisos Web Push de seguimiento y puede abrir la ruta CRM al tocar la notificación.",
        ],
        [
            "Probar la apertura cruzada `/app/` a `/crm/` en dispositivos y navegadores reales usados por el equipo.",
        ],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("ae_push_subscriptions"):
        columns = {column["name"] for column in inspector.get_columns("ae_push_subscriptions")}
        if "installer_email" in columns and "user_email" not in columns:
            op.alter_column("ae_push_subscriptions", "installer_email", new_column_name="user_email")
        indexes = {index["name"] for index in sa.inspect(bind).get_indexes("ae_push_subscriptions")}
        if "ix_ae_push_subscriptions_installer_email" in indexes:
            op.drop_index("ix_ae_push_subscriptions_installer_email", table_name="ae_push_subscriptions")
        indexes = {index["name"] for index in sa.inspect(bind).get_indexes("ae_push_subscriptions")}
        columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_push_subscriptions")}
        if "user_email" in columns and "ix_ae_push_subscriptions_user_email" not in indexes:
            op.create_index("ix_ae_push_subscriptions_user_email", "ae_push_subscriptions", ["user_email"])

    if sa.inspect(bind).has_table("ae_followups"):
        columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_followups")}
        if "push_claimed_at" not in columns:
            op.add_column("ae_followups", sa.Column("push_claimed_at", sa.DateTime(timezone=True), nullable=True))
        if "push_notified_at" not in columns:
            op.add_column("ae_followups", sa.Column("push_notified_at", sa.DateTime(timezone=True), nullable=True))

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
