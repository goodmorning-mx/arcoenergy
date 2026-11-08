"""Record detailed operational report views in the source card history.

Revision ID: 202611080068
Revises: 202611080067
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080068"
down_revision = "202611080067"
branch_labels = None
depends_on = None

ITERATION = "Iteración 57 · detalle de reportes operativos · 2026-11-08"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-29")
        .order_by(history.c.version.desc())
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
            "El informe operativo lista clientes por estado, proveedores y condiciones de pago, órdenes por cliente/folio/estado y gastos detallados dentro del periodo consultado.",
            "Las tablas de detalle omiten teléfono, domicilio, RFC, correo, notas privadas y referencias directas de documentos que no son necesarias para el informe.",
            "Las tarjetas de clientes, proveedores y órdenes son una fotografía actual; los movimientos de gasto conservan el filtro por fecha aplicado.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar con contabilidad si requiere otros campos de detalle o exportaciones dedicadas para clientes, proveedores, órdenes y gastos.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
