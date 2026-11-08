"""Record PWA and offline expense receipt handling in source cards.

Revision ID: 202611080071
Revises: 202611080070
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080071"
down_revision = "202611080070"
branch_labels = None
depends_on = None

ITERATION = "Iteración 59 · comprobantes de gastos desde la PWA · 2026-11-08"

REVISIONS = {
    "US-10": (
        [
            "La PWA de campo admite adjuntar un comprobante PDF/JPG/PNG/WebP de hasta 12 MiB al registrar viáticos y gastos de una orden asignada.",
            "Sin conexión, el gasto idempotente y el archivo quedan en IndexedDB bajo la identidad de la cuenta; al recuperar red, ambos se envían y se retiran de la cola solo tras la confirmación del servidor y Drive.",
            "Si el gasto se confirma pero Drive falla, el archivo permanece en la cola local para reintento sin duplicar el gasto.",
        ],
        [
            "La política de revisión, aprobación y conservación de comprobantes de campo sigue pendiente de validación con contabilidad.",
            "Drive requiere configuración de credenciales y carpeta autorizada en DEV para confirmar el archivado real.",
        ],
    ),
    "US-13": (
        [
            "El flujo de comprobantes de gastos de campo ya puede usar el almacenamiento privado de Drive desde CRM y PWA, incluso después de una captura offline.",
        ],
        [
            "La sincronización general de datos operativos, documentos legales, retención y restauración sigue pendiente.",
        ],
    ),
    "US-17": (
        [
            "El registro móvil de gastos acepta un comprobante opcional y conserva el archivo local hasta que Drive confirme la carga.",
        ],
        [
            "La política contable para aprobar o rechazar comprobantes y gastos de campo sigue pendiente.",
        ],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
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
