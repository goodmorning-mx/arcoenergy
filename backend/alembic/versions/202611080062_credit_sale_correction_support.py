"""Allow source-linked correction of unpaid credit sales.

Revision ID: 202611080062
Revises: 202611070061
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080062"
down_revision = "202611070061"
branch_labels = None
depends_on = None

ITERATION = "Iteración 51 · corrección de venta a crédito sin cobranza activa · 2026-11-08"


def upgrade() -> None:
    column = next((item for item in sa.inspect(op.get_bind()).get_columns("ae_sale_corrections")
                   if item["name"] == "cash_movement_id"), None)
    if column is not None and not column["nullable"]:
        with op.batch_alter_table("ae_sale_corrections") as batch:
            batch.alter_column("cash_movement_id", existing_type=sa.String(36), nullable=True)

    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-11": (
            ["Al corregir una venta financiada sin cobranza neta, sus cuotas dejan de presentarse como saldo pendiente; los pagos recibidos deben corregirse antes desde su historial."],
            ["Intereses, fórmulas validadas de cada plan y avisos automáticos de vencimiento siguen pendientes."],
        ),
        "US-15": (
            ["Una venta a crédito se puede corregir antes de que inicie el trabajo de campo cuando todas sus cuotas siguen sin saldo pagado neto; la cartera se excluye en la misma corrección."],
            ["Las ventas de crédito con cobros activos deben revertir primero cada pago; las órdenes con actividad física permanecen bloqueadas."],
        ),
        "US-16": (
            ["La cartera oculta las cuotas de una venta a crédito corregida y no admite nuevos cobros sobre esos folios, conservando los registros originales."],
            ["Distribuir un pago entre varias ventas y aprobar condiciones de financiamiento sigue pendiente."],
        ),
        "US-35": (
            ["La corrección de venta a crédito sin cobro neto elimina el saldo visible de clientes por cobrar y conserva venta, cuotas, orden y motivo; cobros previos requieren reversa enlazada."],
            ["No se corrigen ventas con pagos netos activos ni órdenes con actividad de campo."],
        ),
        "US-36": (
            ["Ventas a crédito pueden corregirse desde el origen solo después de revertir sus pagos y antes del movimiento físico de inventario; la cartera deja de ofrecer cuotas canceladas."],
            ["Reversas con actividad de campo e inventario, compras y otros efectos contables requieren ciclos específicos."],
        ),
        "US-38": (
            ["La corrección de venta financiada se registra como importe compensatorio en su fecha y proyecto; el neto de la venta y su cartera quedan cancelados."],
            ["El informe sigue siendo preliminar y no incluye impuestos, intereses ni devoluciones/bonificaciones."],
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
    bind = op.get_bind()
    has_null_links = bind.execute(sa.text("SELECT 1 FROM ae_sale_corrections WHERE cash_movement_id IS NULL LIMIT 1")).first()
    if has_null_links:
        raise RuntimeError("Cannot downgrade credit sale corrections while correction rows have no cash movement.")
    column = next((item for item in sa.inspect(bind).get_columns("ae_sale_corrections")
                   if item["name"] == "cash_movement_id"), None)
    if column is not None and column["nullable"]:
        with op.batch_alter_table("ae_sale_corrections") as batch:
            batch.alter_column("cash_movement_id", existing_type=sa.String(36), nullable=False)
