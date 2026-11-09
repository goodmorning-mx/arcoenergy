"""Record browser reminders for due CRM follow-ups.

Revision ID: 202611090075
Revises: 202611090074
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611090075"
down_revision = "202611090074"
branch_labels = None
depends_on = None

ITERATION = "Iteración 63 · avisos de seguimiento en CRM · 2026-11-09"
REVISIONS = {
    "US-4": (
        [
            "La persona responsable puede autorizar avisos del navegador para sus seguimientos vencidos o programados para hoy.",
            "Mientras el CRM permanece abierto, consulta la agenda cada minuto y presenta una notificación genérica sin incluir nombre ni comentario del cliente; cada seguimiento se avisa una vez por cuenta y navegador.",
        ],
        [
            "Los avisos cuando el CRM está cerrado requieren acordar un canal (push, correo o WhatsApp) y validar su entrega en dispositivos/cuentas reales.",
        ],
    ),
    "US-39": (
        [
            "El CRM ofrece avisos de seguimiento del navegador con autorización explícita de la persona y conserva la bandeja de seguimientos como fuente operativa.",
        ],
        [
            "Falta validar los recordatorios con el equipo comercial real; las notificaciones no operan con el CRM cerrado.",
        ],
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
