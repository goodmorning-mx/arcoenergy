"""Record reviewable PDF/photo invoice field candidates for US-22.

Revision ID: 202611110104
Revises: 202611110103
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611110104"
down_revision = "202611110103"
branch_labels = None
depends_on = None

ITERATION = "Iteración 92 · candidatos estructurados de factura · 2026-11-11"


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
            "Mostrar como candidatos revisables los RFC, folio/UUID, fecha de emisión y total detectados en PDF/foto, indicando el texto fuente.",
            "Permitir aplicar cada candidato explícitamente al formulario solo después de revisión humana; el total declarado es referencia y no modifica los renglones contables.",
            "Mantener el archivo OCR en memoria y no crear compras ni movimientos contables durante lectura o aplicación de candidatos.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar candidatos con facturas reales y decidir reglas contables de impuestos, fletes, descuentos y conceptos; estos campos continúan manuales fuera de CFDI XML.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
