"""Add inventory subcategories and append the related US-20 revision.

Revision ID: 202611100081
Revises: 202611100080
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100081"
down_revision = "202611100080"
branch_labels = None
depends_on = None

ITERATION = "Iteración 69 · ficha de inventario y alta desde compras · 2026-11-10"
CRITERIA = [
    "El catálogo de inventario conserva una subcategoría además de categoría y los demás datos descriptivos.",
    "Desde una entrada de compra, un usuario autorizado puede dar de alta un artículo faltante sin registrar existencia inicial; la compra posterior registra cantidades y costos como movimientos normales.",
]
QUESTIONS = [
    "Validar con almacén los nombres de categoría y subcategoría, y probar impresión/lectura de etiquetas con sus dispositivos reales.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("ae_inventory"):
        columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_inventory")}
        if "subcategory" not in columns:
            op.add_column("ae_inventory", sa.Column("subcategory", sa.String(length=100), nullable=False, server_default=""))
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-20").order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
        "acceptance_criteria": [*original["acceptance_criteria"], *CRITERIA],
        "unresolved_questions": [*original["unresolved_questions"], *QUESTIONS],
        "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
