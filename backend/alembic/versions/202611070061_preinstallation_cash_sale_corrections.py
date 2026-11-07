"""Record source-linked corrections for pre-installation cash sales.

Revision ID: 202611070061
Revises: 202611070060
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070061"
down_revision = "202611070060"
branch_labels = None
depends_on = None

ITERATION = "Iteración 50 · corrección de venta de contado antes de instalación · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    sa.Table("ae_sales", metadata, autoload_with=bind)
    sa.Table("ae_cash_movements", metadata, autoload_with=bind)
    correction_table = sa.Table(
        "ae_sale_corrections", metadata,
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sale_id", sa.String(36), sa.ForeignKey("ae_sales.id"), nullable=False),
        sa.Column("cash_movement_id", sa.String(36), sa.ForeignKey("ae_cash_movements.id"), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("reason", sa.String(120), nullable=False),
        sa.Column("created_by", sa.String(180), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("sale_id", name="uq_ae_sale_correction_sale"),
        sa.UniqueConstraint("cash_movement_id", name="uq_ae_sale_correction_cash_movement"),
    )
    if not sa.inspect(bind).has_table("ae_sale_corrections"):
        op.execute(sa.schema.CreateTable(correction_table))

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-15": (
            ["Una venta de contado puede corregirse desde su origen, antes de cualquier actividad de instalación, agregando una reversa de caja y una cancelación de la reserva; venta y folio originales permanecen consultables."],
            ["La corrección de ventas a crédito y ventas con materiales ya emitidos requiere un flujo específico que considere cobranza, devolución y costo."],
        ),
        "US-18": (
            ["La reversa de venta de contado se registra en la misma cuenta de caja/banco, enlazada al ingreso original y con motivo obligatorio."],
            ["Conciliación bancaria y corrección de ventas a crédito siguen pendientes."],
        ),
        "US-32": (
            ["La corrección conserva folio de venta y orden; la orden queda cancelada con una referencia auditable y su reserva deja de comprometer existencia disponible."],
            ["La entidad de proyecto independiente y formato comercial de folio siguen sujetos a definición."],
        ),
        "US-35": (
            ["La venta de contado preinstalación se corrige en origen, restituye caja y libera materiales reservados en una transacción; se bloquea si hay avances de campo."],
            ["Faltan correcciones para ventas a crédito y movimientos físicos/inventario ya ejecutados."],
        ),
        "US-36": (
            ["El sistema conserva la venta y agrega una corrección única con motivo, junto con movimiento inverso de caja y registro de cancelación de la orden."],
            ["No se permiten reversas integrales cuando la venta tiene cobranza, emisión o consumo de materiales; esos ciclos siguen pendientes."],
        ),
        "US-38": (
            ["El costeo por periodo incorpora la corrección de venta en la fecha en que se registra; el resultado histórico del proyecto conserva ambas fechas."],
            ["El resultado sigue siendo preliminar y no incluye impuestos, devoluciones de venta ni bonificaciones."],
        ),
    }
    for story_id, (criteria, questions) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
    op.drop_table("ae_sale_corrections")
