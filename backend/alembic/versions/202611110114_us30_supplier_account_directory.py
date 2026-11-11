"""Record delivery of supplier directory and payable criteria for US-30.

Revision ID: 202611110114
Revises: 202611110113
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110114"
down_revision = "202611110113"
branch_labels = None
depends_on = None

ITERATION = "Iteración 102 · directorio y saldos de proveedores · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-30").order_by(history.c.version.desc())
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
            "CRM permite listar y dar de alta proveedores con condición de contado o crédito y días acordados.",
            "El directorio muestra saldo pendiente calculado desde compras y pagos asociados al proveedor.",
            "Un proveedor con historial se conserva para que sus compras y pagos sigan consultables.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "El cliente debe confirmar si se requiere desactivar/archivar proveedores y qué campos adicionales desea ver en su directorio.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
