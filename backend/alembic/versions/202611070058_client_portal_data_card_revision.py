"""Record customer portal response minimization.

Revision ID: 202611070058
Revises: 202611070057
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070058"
down_revision = "202611070057"
branch_labels = None
depends_on = None

ITERATION = "Iteración 47 · datos mínimos en portal de cliente · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-14": (
            ["El portal de cliente recibe solo campos necesarios para consultar sus cotizaciones, avance de instalación y pagos; no expone costos internos, notas de coordinación, correo de instaladores ni IDs de archivos privados."],
            ["Falta ejecutar pruebas de aislamiento con cuentas reales de cada rol y validar la matriz completa con responsables del negocio."],
        ),
        "US-40": (
            ["La vista PWA de cliente conserva cotizaciones, estado de órdenes, checklist y vencimientos mediante una respuesta del API reducida a campos de presentación."],
            ["Se requiere probar navegación y experiencia con cuentas reales de clientes."],
        ),
    }
    for story_id, (criteria, questions) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
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
