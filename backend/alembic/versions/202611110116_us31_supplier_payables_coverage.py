"""Record verified supplier payable and payment criteria for US-31.

Revision ID: 202611110116
Revises: 202611110115
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110116"
down_revision = "202611110115"
branch_labels = None
depends_on = None

ITERATION = "Iteración 104 · compras, saldos y pagos a proveedores · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-31").order_by(history.c.version.desc())
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
            "Una compra a crédito queda vinculada al proveedor, agrega inventario y aumenta su saldo pendiente.",
            "El pago se captura ligado a una compra con fecha, importe y cuenta de caja/banco; reduce por el mismo importe la cuenta por pagar y el saldo de la cuenta.",
            "La compra y sus pagos conservan folio, historial y correcciones enlazadas.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La conciliación bancaria y el manejo de diferencias contra estados de cuenta requieren definición contable.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
