"""Record accurate status for incomplete external integrations.

Revision ID: 202611070049
Revises: 202611070048
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070049"
down_revision = "202611070048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-13")
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 38 · estado honesto de integraciones externas · 2026-11-07",
        "acceptance_criteria": [*original["acceptance_criteria"],
            "La API no declara Google Drive conectado por tener configurado solo el ID de carpeta; la subida y lectura de archivos siguen sin implementar.",
            "El modo disponible de WhatsApp se identifica como abrir chat; no se declara conexión de envío automático."],
        "unresolved_questions": [*original["unresolved_questions"],
            "Faltan credenciales/permiso de servicio, política de acceso y pruebas de almacenamiento para integrar Google Drive.",
            "La carga de datos operacionales a Drive requiere definir alcance, sincronización y fuente autoritativa."],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 38 · estado honesto de integraciones externas · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
