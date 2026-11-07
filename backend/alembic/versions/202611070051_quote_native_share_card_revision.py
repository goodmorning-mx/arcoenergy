"""Record native quote PDF sharing while preserving stakeholder source.

Revision ID: 202611070051
Revises: 202611070050
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070051"
down_revision = "202611070050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-3")
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 40 · compartir PDF de cotización desde app/CRM · 2026-11-07",
        "acceptance_criteria": [*original["acceptance_criteria"],
            "Desde CRM y PWA se puede invocar el diálogo nativo para compartir el PDF como archivo con WhatsApp u otra aplicación compatible.",
            "Si el navegador no admite compartir archivos, se descarga el PDF y se abre WhatsApp con un mensaje preparado; el vendedor adjunta el archivo y confirma el envío."],
        "unresolved_questions": [*original["unresolved_questions"],
            "El diálogo nativo depende de compatibilidad del navegador/dispositivo y de que WhatsApp esté instalado o disponible como destino.",
            "La integración no envía mensajes en segundo plano ni confirma que el destinatario haya recibido el documento."],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 40 · compartir PDF de cotización desde app/CRM · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
