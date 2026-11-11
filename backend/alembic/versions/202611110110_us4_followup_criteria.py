"""Record completed follow-up scheduling criteria for US-4.

Revision ID: 202611110110
Revises: 202611110109
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110110"
down_revision = "202611110109"
branch_labels = None
depends_on = None

ITERATION = "Iteración 98 · cobertura del seguimiento comercial · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-4").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "El CRM puede programar el contacto en 3, 7, 15 o 30 días, o elegir una fecha futura libre.",
            "Cada seguimiento conserva el comentario/motivo y aparece en la ficha del cliente junto con notas y actividad de bitácora.",
            "El seguimiento se asigna a un responsable autorizado y queda disponible en la agenda/lista del CRM.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar notificaciones con vendedores autenticados en los dispositivos de uso; el registro y la agenda no dependen de que el aviso push llegue.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
