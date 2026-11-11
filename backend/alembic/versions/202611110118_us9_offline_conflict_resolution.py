"""Record offline conflict resolution coverage for US-9.

Revision ID: 202611110118
Revises: 202611110117
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110118"
down_revision = "202611110117"
branch_labels = None
depends_on = None

ITERATION = "Iteración 106 · resolución de conflictos offline · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-9").order_by(history.c.version.desc())
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
            "Una acción rechazada por el servidor conserva localmente su estado y detalle para que el instalador pueda revisarla después de cerrar o recargar la PWA.",
            "El instalador puede corregir la cantidad de un consumo o devolución rechazado y reintentar con el mismo identificador de operación; el servidor valida la cantidad contra el estado vigente.",
            "Una operación pendiente rechazada pausa las acciones posteriores; el usuario puede retirar una acción individual tras revisar el mensaje, y el resto conserva su orden.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La resolución y observación de conflictos requiere validación de campo en teléfonos reales y escenarios de sincronización simultánea.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
