"""Record delivery of expense capture criteria for US-17.

Revision ID: 202611110112
Revises: 202611110111
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110112"
down_revision = "202611110111"
branch_labels = None
depends_on = None

ITERATION = "Iteración 100 · cobertura del registro de gastos · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-17").order_by(history.c.version.desc())
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
            "CRM y PWA capturan fecha, importe, descripción, categoría y clasificación fija/variable del gasto.",
            "El gasto se vincula con una cuenta de efectivo/banco y opcionalmente con proyecto u orden de trabajo.",
            "Los gastos de campo pueden adjuntar comprobante; CRM/PWA muestran la disponibilidad del archivo y el estado de archivado en Drive.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Contabilidad debe validar clasificación de gastos mixtos, recurrencia y política de aprobación de comprobantes.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
