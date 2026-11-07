"""Keep expense corrections linked to the original entry.

Revision ID: 202611070060
Revises: 202611070059
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070060"
down_revision = "202611070059"
branch_labels = None
depends_on = None

ITERATION = "Iteración 49 · corrección enlazada de gastos · 2026-11-07"


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_expenses")}
    if "reversal_of_id" not in columns:
        with op.batch_alter_table("ae_expenses") as batch:
            batch.add_column(sa.Column("reversal_of_id", sa.String(36), nullable=True))
            batch.create_foreign_key("fk_ae_expenses_reversal", "ae_expenses", ["reversal_of_id"], ["id"])
            batch.create_unique_constraint("uq_ae_expenses_reversal", ["reversal_of_id"])
            batch.create_index("ix_ae_expenses_reversal_of_id", ["reversal_of_id"])

    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-17": (
            ["El gasto original no se borra: administración o contabilidad puede corregirlo con motivo; se agrega un importe compensatorio enlazado y caja/banco revierte su salida relacionada."],
            ["Reembolsos, anticipos y autorización de gastos de campo siguen pendientes."],
        ),
        "US-18": (
            ["La corrección de un gasto revierte la salida de caja/banco en la misma operación y deja motivo, fecha y referencia al movimiento original."],
            ["Conciliación con estados de cuenta y comisiones bancarias sigue pendiente."],
        ),
        "US-35": (
            ["El gasto se corrige desde su origen con una entrada compensatoria en costo y un movimiento inverso enlazado en la cuenta; no se ofrece reversa suelta que desincronice saldos."],
            ["La corrección integral de ventas, compras e inventario sigue pendiente."],
        ),
        "US-36": (
            ["Los gastos administrativos pueden corregirse una sola vez, con motivo, sin borrar el origen; el historial de gasto, costeo por proyecto y caja/banco se actualizan juntos."],
            ["Faltan correcciones integrales para compras, ventas, cobranza e inventario."],
        ),
        "US-38": (
            ["Una corrección de gasto se conserva como asiento compensatorio y ajusta el costeo del periodo y del proyecto en su fecha de corrección."],
            ["El resultado sigue siendo preliminar y no sustituye el cierre contable."],
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
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_expenses")}
    if "reversal_of_id" in columns:
        with op.batch_alter_table("ae_expenses") as batch:
            batch.drop_index("ix_ae_expenses_reversal_of_id")
            batch.drop_constraint("uq_ae_expenses_reversal", type_="unique")
            batch.drop_constraint("fk_ae_expenses_reversal", type_="foreignkey")
            batch.drop_column("reversal_of_id")
