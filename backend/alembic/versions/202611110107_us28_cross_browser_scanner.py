"""Record cross-browser camera decoding for US-28.

Revision ID: 202611110107
Revises: 202611110106
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110107"
down_revision = "202611110106"
branch_labels = None
depends_on = None

ITERATION = "Iteración 95 · escáner de cámara entre navegadores · 2026-11-11"


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
            "La cámara puede decodificar códigos en navegadores sin BarcodeDetector mediante un lector local cargado al abrir el escáner.",
            "Escanear solo identifica el artículo; no registra salidas ni modifica inventario.",
            "La captura manual y los lectores que escriben en el campo siguen disponibles como alternativa.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar en los modelos de teléfono, navegadores, lectores y etiquetas reales de ArcoEnergy; comprobar disponibilidad de cámara en uso sin conexión.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
