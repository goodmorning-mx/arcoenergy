"""Record review-only invoice text extraction for US-22.

Revision ID: 202611110103
Revises: 202611110102
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611110103"
down_revision = "202611110102"
branch_labels = None
depends_on = None

ITERATION = "Iteración 91 · lectura asistida de factura PDF/foto · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-22").order_by(history.c.version.desc())
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
            "Leer texto de PDF con capa de texto y aplicar OCR en español/inglés a facturas escaneadas o fotografiadas.",
            "Mostrar el resultado como transcripción temporal que la persona revisa y captura manualmente antes de registrar la compra.",
            "Limitar tipo, tamaño, páginas y pixeles; no guardar el archivo ni crear movimientos desde la lectura OCR.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar precisión OCR con facturas reales de los proveedores de ArcoEnergy y decidir después si campos específicos pueden precargarse.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
