"""Support source-linked corrections for purchases before stock use.

Revision ID: 202611080064
Revises: 202611080063
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080064"
down_revision = "202611080063"
branch_labels = None
depends_on = None

ITERATION = "Iteración 53 · corrección de compras antes de movimiento de almacén · 2026-11-08"


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("ae_purchase_lines") and "previous_unit_cost" not in {
        column["name"] for column in sa.inspect(bind).get_columns("ae_purchase_lines")
    }:
        op.add_column("ae_purchase_lines", sa.Column("previous_unit_cost", sa.Numeric(12, 2), nullable=True))
    if not sa.inspect(bind).has_table("ae_purchase_corrections"):
        op.create_table(
            "ae_purchase_corrections",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("purchase_id", sa.String(length=36), nullable=False),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("reason", sa.String(length=120), nullable=False),
            sa.Column("created_by", sa.String(length=180), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["purchase_id"], ["ae_purchases.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("purchase_id", name="uq_ae_purchase_correction_purchase"),
        )
        op.create_index(
            "ix_ae_purchase_corrections_purchase_id",
            "ae_purchase_corrections",
            ["purchase_id"],
        )

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-21": ("Una compra corregida conserva la factura y los renglones; la corrección de almacén se agrega como movimiento relacionado.", "El tratamiento de impuestos, fletes y descuentos sigue requiriendo reglas contables.") ,
        "US-31": ("La corrección de una compra sin saldo pagado neto restaura existencias y elimina su saldo abierto de proveedor; los pagos deben revertirse primero.", "Las compras con movimientos posteriores de almacén requieren conciliación y siguen bloqueadas.") ,
        "US-35": ("La corrección de compra enlaza cuenta por pagar, renglones y entradas de almacén en una sola operación auditable.", "No sustituye pólizas de doble partida ni conciliación contable formal.") ,
        "US-36": ("Administración o contabilidad puede corregir una compra antes de uso posterior del material; conserva factura, renglones y pagos originales, y agrega reversas enlazadas.", "Si hubo pagos activos se deben revertir primero; si el inventario tuvo movimientos posteriores, se requiere un flujo específico de devolución/ajuste.") ,
        "US-38": ("La corrección de compra retira su existencia y valor unitario cuando el material sigue sin movimientos posteriores.", "El estado de resultados sigue siendo preliminar y requiere validar valoración y clasificación con contabilidad.") ,
    }
    for story_id, (criterion, question) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], criterion],
            "unresolved_questions": [*original["unresolved_questions"], question],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
    if not sa.inspect(op.get_bind()).has_table("ae_purchase_corrections"):
        return
    has_corrections = op.get_bind().execute(sa.text("SELECT 1 FROM ae_purchase_corrections LIMIT 1")).first()
    if has_corrections:
        raise RuntimeError("Cannot downgrade while purchase corrections exist.")
    op.drop_table("ae_purchase_corrections")
