"""Record live DEV verification of the public solar quote assistant.

Revision ID: 202611080065
Revises: 202611080064
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080065"
down_revision = "202611080064"
branch_labels = None
depends_on = None

ITERATION = "Iteración 54 · verificación del agente público y catálogo comercial · 2026-11-08"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history)
        .where(history.c.story_id == "US-41")
        .order_by(history.c.version.desc())
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
            "En DEV, el chat público respondió en español por HTTP 200 al consultar los tamaños de sistema usando el agente configurado.",
            "Al solicitar una cotización de 8 paneles sin paquete comercial activo y aprobado, el asistente informó que no puede cotizar; no inventó un precio ni creó una cotización o un prospecto.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "El catálogo consultado no ofrece un paquete activo y aprobado de 8 paneles. Administración debe cargar y aprobar los datos comerciales reales (paquetes, inversores y formas de pago) antes de que la web pueda dar una cotización.",
            "Queda pendiente verificar captura de prospecto con consentimiento desde el formulario público y cotejar los tamaños/precios con el responsable comercial.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table(
        "ae_history_cards",
        sa.column("iteration", sa.String()),
        sa.column("recorded_by", sa.String()),
    )
    op.execute(
        sa.delete(history).where(
            history.c.iteration == ITERATION,
            history.c.recorded_by == "system:implementation-iteration",
        )
    )
