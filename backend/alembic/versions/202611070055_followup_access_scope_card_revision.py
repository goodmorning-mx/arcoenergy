"""Record ownership rules for customer follow-ups.

Revision ID: 202611070055
Revises: 202611070054
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070055"
down_revision = "202611070054"
branch_labels = None
depends_on = None

ITERATION = "Iteración 44 · acceso a seguimientos por responsable · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-4": (
            ["La lista de seguimientos y su actualización quedan limitadas a la persona responsable; administración conserva visibilidad y gestión global."],
            ["El recordatorio automático fuera del CRM y las notificaciones push quedan pendientes de canal y configuración."],
        ),
        "US-14": (
            ["El API limita el acceso y actualización de seguimientos al responsable asignado; administración puede consultar y reasignar cualquier seguimiento."],
            ["La matriz completa por entidad/campo todavía requiere validación de stakeholders y cuentas reales de cada rol."],
        ),
    }
    for story_id, (criteria, questions) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
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
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
