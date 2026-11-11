"""Record deliberate quote PDF sharing and reliable WhatsApp fallback for US-3.

Revision ID: 202611110105
Revises: 202611110104
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611110105"
down_revision = "202611110104"
branch_labels = None
depends_on = None

ITERATION = "Iteración 93 · compartir cotización con confirmación · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-3").order_by(history.c.version.desc())
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
            "Después de preparar el PDF, mostrar una confirmación de canal y abrir el selector nativo desde un gesto explícito de la persona.",
            "Ofrecer un enlace de WhatsApp que descarga el PDF y prepara el mensaje en el mismo gesto, para evitar bloqueos de ventanas emergentes después de llamadas de red.",
            "Informar si Drive archivó el PDF, falló el archivo o no está configurado; no afirmar que se envió hasta que la persona lo confirme en WhatsApp.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Validar compartir archivos y adjuntar el PDF en dispositivos reales de ArcoEnergy; envío automático y confirmación por API siguen dependiendo de integración aprobada.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
