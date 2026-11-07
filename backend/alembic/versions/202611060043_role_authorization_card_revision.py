"""Record live membership authorization checks for role changes.

Revision ID: 202611060043
Revises: 202611060042
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060043"
down_revision = "202611060042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-14").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 32 · validación de autorización por rol · 2026-11-06",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "La autorización vuelve a comprobar los permisos de la membresía activa en el API; un token con permisos obsoletos no conserva acceso tras cambiar el rol y una membresía desactivada no autoriza solicitudes.",
            "El inventario y kardex omiten el costo unitario para instaladores y lo incluyen para contabilidad, según los permisos efectivos.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta recorrer la matriz de entidades y campos con usuarios reales de contador, marketing, administrador, instalador y cliente.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 32 · validación de autorización por rol · 2026-11-06",
        history.c.recorded_by == "system:implementation-iteration",
    ))
