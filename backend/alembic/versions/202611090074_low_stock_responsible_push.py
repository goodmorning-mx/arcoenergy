"""Assign inventory restock owner and push on low-stock threshold crossings.

Revision ID: 202611090074
Revises: 202611080073
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611090074"
down_revision = "202611080073"
branch_labels = None
depends_on = None

ITERATION = "Iteración 62 · responsables y avisos de reabasto · 2026-11-09"
REVISIONS = {
    "US-26": (
        [
            "Administración puede asignar a cada artículo un responsable de reposición que sea una cuenta activa de instalador.",
            "Cuando la existencia disponible cruza el mínimo configurado, el responsable suscrito recibe un aviso Web Push con artículo, existencia y mínimo; se evita repetir el aviso mientras el stock siga bajo el umbral.",
            "Al recuperarse el stock por encima del mínimo, el estado de alerta se rearma para una futura caída.",
        ],
        ["Confirmar en teléfonos reales la entrega push y validar si almacén debe poder asignar responsables con un rol distinto al instalador."],
    ),
    "US-40": (
        ["La PWA del instalador puede recibir avisos push de reposición cuando los artículos que tiene asignados cruzan su mínimo configurado.",
         "Si el instalador activa avisos después de que un artículo ya está debajo del mínimo, recibe el aviso al registrar el dispositivo."],
        ["Validar la recepción en segundo plano con los dispositivos reales del equipo."],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("ae_inventory"):
        columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_inventory")}
        if "restock_responsible_email" not in columns:
            op.add_column("ae_inventory", sa.Column("restock_responsible_email", sa.String(180), nullable=False, server_default=""))
        if "low_stock_alert_active" not in columns:
            op.add_column("ae_inventory", sa.Column("low_stock_alert_active", sa.Boolean(), nullable=False, server_default=sa.false()))
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
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
