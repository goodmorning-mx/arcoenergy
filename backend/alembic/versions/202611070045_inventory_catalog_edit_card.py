"""Record controlled inventory catalog edits as a US-20 iteration.

Revision ID: 202611070045
Revises: 202611060044
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070045"
down_revision = "202611060044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-20")
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 34 · mantenimiento de ficha de materiales · 2026-11-07",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Administración puede corregir los datos descriptivos y de identificación del material y reasignar su proveedor desde CRM.",
            "El catálogo no permite alterar existencias directamente: las cantidades cambian únicamente con movimientos de entrada, salida, consumo o devolución.",
            "La edición valida la unicidad del código QR/barcode y conserva los movimientos históricos aunque cambie la ficha actual.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta validar con almacén las unidades de medida permitidas y su impresión/lectura en equipos reales.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 34 · mantenimiento de ficha de materiales · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
