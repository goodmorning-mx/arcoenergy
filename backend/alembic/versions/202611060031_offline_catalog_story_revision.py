"""Record offline barcode lookup enabled by the field catalog cache.

Revision ID: 202611060031
Revises: 202611060030
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060031"
down_revision = "202611060030"
branch_labels = None
depends_on = None

ITERATION = "Iteración 20 · sincronización segura de operaciones de campo · 2026-11-07"
STORY_ID = "US-28"
NOTE = (
    "La PWA conserva por cuenta el catálogo de inventario consultado previamente; el lector QR/barras "
    "puede buscar en esa caché sin conexión. Requiere una consulta autenticada previa. Pendiente validar "
    "formatos y navegadores en teléfonos y lectores reales de ArcoEnergy."
)


def upgrade() -> None:
    table = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=op.get_bind())
    bind = op.get_bind()
    original = bind.execute(
        sa.select(table).where(table.c.story_id == STORY_ID).order_by(table.c.version.desc()).limit(1)
    ).mappings().first()
    if original is None:
        return
    revision_row = dict(original)
    revision_row.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"], f"Nota del equipo, no validada por el stakeholder: {NOTE}"],
        "unresolved_questions": [*original["unresolved_questions"], "Validar cámara, lectores externos y formatos de código en los dispositivos reales de campo."],
        "linked_cards": sorted(set([*original["linked_cards"], "US-9", "US-10", "US-40"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(table, [revision_row])


def downgrade() -> None:
    table = sa.table("ae_history_cards", sa.column("story_id", sa.String()), sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(table).where(table.c.story_id == STORY_ID, table.c.iteration == ITERATION, table.c.recorded_by == "system:implementation-iteration"))
