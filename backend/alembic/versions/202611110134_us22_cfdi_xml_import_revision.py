"""Record the review-only CFDI XML purchase import for US-22.

Revision ID: 202611110134
Revises: 202611110133
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110134"
down_revision = "202611110133"
branch_labels = None
depends_on = None

ITERATION = "Iteración 122 · captura asistida de CFDI XML para compras · 2026-11-11"


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
            "La captura asistida acepta CFDI XML 3.3/4.0 de ingreso en MXN y propone proveedor, referencia, fecha, conceptos y costos para revisión.",
            "Leer XML no crea una compra ni altera inventario; el registro requiere confirmación humana en el formulario.",
            "Diferencias por impuestos, descuentos globales u otros ajustes se marcan para revisión y no se distribuyen automáticamente.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta probar precisión y mapeo con facturas reales de los proveedores de ArcoEnergy.",
            "Contabilidad debe definir cómo asignar impuestos, fletes, descuentos y otros ajustes al costo de los artículos.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
