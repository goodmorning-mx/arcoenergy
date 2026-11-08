"""Record private Drive expense receipt handling in source cards.

Revision ID: 202611080070
Revises: 202611080069
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080070"
down_revision = "202611080069"
branch_labels = None
depends_on = None

ITERATION = "Iteración 58 · comprobantes privados de gastos · 2026-11-08"

REVISIONS = {
    "US-13": (
        [
            "Los gastos pueden adjuntar comprobantes PDF/JPG/PNG/WebP a la carpeta privada de Drive, con descarga autenticada desde CRM.",
            "La respuesta de la API no revela el identificador privado de Drive; si Drive no está configurado, la carga informa el estado sin afirmar que el archivo se respaldó.",
        ],
        [
            "El alcance todavía no sincroniza todos los datos operativos a Drive; faltan política de carpetas, retención, restauración y permisos acordados.",
            "La captura de comprobantes desde PWA/offline y la validación con contabilidad siguen pendientes.",
        ],
    ),
    "US-17": (
        [
            "CRM permite adjuntar un comprobante privado al gasto registrado y volver a intentar la carga si Drive falla.",
            "La descarga del archivo requiere expenses:read y la carga expenses:write; el archivo tiene límite de 12 MiB y se valida tipo y firma básica.",
        ],
        [
            "Validar con contabilidad la política de conservación y el proceso requerido cuando un comprobante no se puede archivar.",
            "El flujo móvil de gastos todavía no adjunta comprobantes; el registro offline continúa disponible sin archivo.",
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
