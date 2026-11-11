"""Record review-only OCR for service material requests.

Revision ID: 202611110106
Revises: 202611110105
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110106"
down_revision = "202611110105"
branch_labels = None
depends_on = None

ITERATION = "Iteración 94 · lectura asistida de solicitud de materiales · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-25").order_by(history.c.version.desc())
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
            "El CRM puede extraer temporalmente texto de una foto o PDF de solicitud para facilitar la revisión previa de los renglones.",
            "La lectura OCR no confirma cantidades, crea movimientos ni modifica existencias; la persona revisa el documento y captura las cantidades antes de confirmar.",
            "Si el documento es ilegible o el OCR no está disponible, la captura manual continúa disponible.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Precisar la calidad del OCR para las solicitudes manuscritas y validar con el formato real del almacén.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
