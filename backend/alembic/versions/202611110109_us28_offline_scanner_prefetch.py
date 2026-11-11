"""Record offline scanner module prefetch for US-28.

Revision ID: 202611110109
Revises: 202611110108
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110109"
down_revision = "202611110108"
branch_labels = None
depends_on = None

ITERATION = "Iteración 97 · preparación offline del escáner · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-28").order_by(history.c.version.desc())
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
            "Al iniciar sesión como instalador con conexión y service worker activo, la PWA precarga el módulo del escáner para permitir abrir la cámara más tarde sin red.",
            "Si la precarga no está disponible, la búsqueda manual sigue funcionando con el inventario cacheado.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar en teléfono real el ciclo conexión, precarga, modo avión y lectura de etiqueta, incluidas las políticas del navegador para cámara y service worker.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
