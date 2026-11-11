"""Record safe public agent-to-contact-form handoff for US-41.

Revision ID: 202611110126
Revises: 202611110125
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110126"
down_revision = "202611110125"
branch_labels = None
depends_on = None

ITERATION = "Iteración 114 · consentimiento y contacto del agente público · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-41").order_by(history.c.version.desc())
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
            "El agente público no solicita ni promete guardar datos de contacto en el chat; dirige al formulario comercial, donde la persona revisa privacidad y consiente el envío de su solicitud.",
            "El agente declara cuando no existe precio aprobado y no inventa precios ni afirma haber registrado una cotización o prospecto.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta que ArcoEnergy configure y apruebe los paquetes comerciales reales para habilitar estimaciones de precio en el agente.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
