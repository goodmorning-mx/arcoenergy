"""Record the public quote catalog readiness audit.

Revision ID: 202611110101
Revises: 202611110100
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110101"
down_revision = "202611110100"
branch_labels = None
depends_on = None

ITERATION = "Iteración 89 · disponibilidad del cotizador público · 2026-11-11"
STORIES = {
    "US-1": (
        ["La consulta agregada al catálogo DEV reportó cero paquetes activos y cero paquetes con precio aprobado."],
        ["ArcoEnergy debe proporcionar marca, potencia, precio vigente, estructura, inversores y formas de pago para los paquetes de 4 a 20 paneles, y aprobarlos antes de habilitar cotizaciones."],
    ),
    "US-41": (
        ["La web muestra el chat de cotización con gm-agent y las herramientas de catálogo basadas en gm-mcp; no se llamó al proveedor durante esta auditoría. El catálogo actual tiene cero paquetes activos y aprobados, por lo que el agente no debe entregar una cotización con precio."],
        ["Probar el recorrido comercial tras cargar y aprobar los paquetes reales, incluido consentimiento del formulario de prospecto."],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in STORIES.items():
        original = bind.execute(
            sa.select(history)
            .where(history.c.story_id == story_id)
            .order_by(history.c.version.desc())
        ).mappings().first()
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
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
