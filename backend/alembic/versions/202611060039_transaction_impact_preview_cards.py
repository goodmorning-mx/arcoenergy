"""Record the pre-action accounting impact summaries as story revisions.

Revision ID: 202611060039
Revises: 202611060038
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060039"
down_revision = "202611060038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    updates = {
        "US-33": (
            "CRM muestra antes de confirmar compras, ventas, pagos a proveedores y cobros de clientes los saldos de almacén, caja/banco y cuentas por pagar/cobrar que modifica cada acción. En una venta el material queda reservado para la orden; la existencia física se descuenta al registrar la salida. El resumen refleja las reglas actuales del sistema y no sustituye la validación contable."
        ),
        "US-35": (
            "Las pantallas de captura anticipan los efectos actuales: compra aumenta existencias, registra el pago inicial en caja/banco y deja el remanente a proveedor; venta de contado aumenta la cuenta seleccionada y reserva materiales en la orden; venta a crédito crea el saldo por cobrar y reserva materiales; los pagos cambian caja/banco y el saldo relacionado. La existencia baja al registrar la salida de material, no al crear la reserva. Impuestos, pagos mixtos y Plan 24 aún requieren reglas aprobadas por contabilidad."
        ),
    }
    for story_id, note in updates.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": "Iteración 28 · vista previa de impactos operativos · 2026-11-06",
            "acceptance_criteria": [
                *original["acceptance_criteria"],
                f"Nota de implementación del equipo, pendiente de validación con contabilidad: {note}",
            ],
            "unresolved_questions": [
                *original["unresolved_questions"],
                "Validar importes, impuestos, pagos mixtos, Plan 24 y reglas de afectación con el contador antes de usarlos como estados financieros oficiales.",
            ],
            "linked_cards": sorted(set([*original["linked_cards"], "US-33", "US-35"])),
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 28 · vista previa de impactos operativos · 2026-11-06",
        history.c.recorded_by == "system:implementation-iteration",
    ))
