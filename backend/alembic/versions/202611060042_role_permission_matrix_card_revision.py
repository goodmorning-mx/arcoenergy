"""Record the visible CRM role permission matrix without changing its source.

Revision ID: 202611060042
Revises: 202611060041
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060042"
down_revision = "202611060041"
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
        "iteration": "Iteración 31 · matriz visible de permisos por rol · 2026-11-06",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "CRM consulta /team/roles y muestra los permisos efectivos de los cinco roles; las etiquetas traducen cada permiso y la autorización sigue aplicándose en el API.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La matriz describe presets globales, no permisos configurables por usuario. Falta validar todas las reglas de acceso con cuentas reales de cada rol y con sus responsables.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 31 · matriz visible de permisos por rol · 2026-11-06",
        history.c.recorded_by == "system:implementation-iteration",
    ))
