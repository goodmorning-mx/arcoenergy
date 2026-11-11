"""Record static API authorization coverage for US-14.

Revision ID: 202611110119
Revises: 202611110118
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110119"
down_revision = "202611110118"
branch_labels = None
depends_on = None

ITERATION = "Iteración 107 · inventario de autorización de rutas API · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
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
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Una prueba de auditoría inspecciona todas las rutas HTTP /v1 del producto y falla si una ruta privada no declara una dependencia de permiso explícita.",
            "Solo las rutas públicas de captación y chat incluidas en una lista explícita pueden quedar sin autorización de sesión; las rutas de suscripción push requieren permiso en la firma del endpoint.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La revisión estática de rutas complementa, pero no sustituye, la matriz validada por ArcoEnergy ni las pruebas autenticadas de cada rol con cuentas reales.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
