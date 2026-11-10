"""Store accountable, reversible profitability adjustments.

Revision ID: 202611100079
Revises: 202611090078
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100079"
down_revision = "202611090078"
branch_labels = None
depends_on = None

ITERATION = "Iteración 67 · devoluciones y bonificaciones en resultado · 2026-11-10"
CRITERIA = [
    "El reporte preliminar por mes y proyecto incluye las devoluciones y bonificaciones registradas como un concepto separado y sumado según la fórmula literal compartida por contabilidad.",
    "Contabilidad puede agregar y corregir estos ajustes; las correcciones agregan un movimiento de reversa y mantienen el historial original.",
    "Registrar un ajuste de rentabilidad no genera por sí mismo movimientos de caja ni cambia una venta; el reporte sigue identificado como preliminar.",
]
QUESTIONS = [
    "Validar con el contador los tipos, documentos de soporte y tratamiento contable de devoluciones y bonificaciones antes de considerar formal cualquier estado de resultados.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_profitability_adjustments"):
        op.create_table(
            "ae_profitability_adjustments",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("installation_id", sa.String(length=36), sa.ForeignKey("ae_installations.id"), nullable=True),
            sa.Column("adjustment_type", sa.String(length=20), nullable=False),
            sa.Column("description", sa.String(length=240), nullable=False),
            sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
            sa.Column("occurred_on", sa.Date(), nullable=False),
            sa.Column("reversal_of_id", sa.String(length=36), sa.ForeignKey("ae_profitability_adjustments.id"), nullable=True),
            sa.Column("created_by", sa.String(length=180), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("reversal_of_id", name="uq_ae_profitability_adjustment_reversal"),
        )
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("ae_profitability_adjustments")}
    for name, column in (("ix_ae_profitability_adjustments_installation_id", "installation_id"), ("ix_ae_profitability_adjustments_reversal_of_id", "reversal_of_id")):
        if name not in indexes:
            op.create_index(name, "ae_profitability_adjustments", [column])

    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-38").order_by(history.c.version.desc())).mappings().first()
    if original is not None:
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
