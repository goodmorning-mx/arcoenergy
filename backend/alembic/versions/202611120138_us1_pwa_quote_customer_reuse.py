"""Record customer reuse from the PWA quote flow for US-1 and US-3.

Revision ID: 202611120138
Revises: 202611120137
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611120138"
down_revision = "202611120137"
branch_labels = None
depends_on = None

ITERATION = "Iteración 126 · reutilización de clientes en cotizador PWA · 2026-11-12"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, criteria, questions in (
        (
            "US-1",
            [
                "Desde la PWA, el vendedor puede elegir una ficha de cliente existente antes de generar una propuesta.",
                "Al elegir una ficha existente, nombre, teléfono y correo se conservan vinculados a ese cliente; el lugar de instalación sigue editable.",
                "Si la cotización falla después de crear un cliente nuevo, un reintento reutiliza la ficha creada y no duplica el cliente.",
            ],
            ["Falta validar el flujo con cartera y cuentas comerciales reales de ArcoEnergy en DEV."],
        ),
        (
            "US-3",
            [
                "La cotización PWA se asocia a la ficha seleccionada o a la ficha nueva creada para esa propuesta.",
                "Al cambiar el cliente seleccionado se limpia el folio/PDF anterior para evitar compartir el documento de otra propuesta.",
            ],
            ["La integración y almacenamiento empresarial en Google Drive siguen pendientes de credenciales y carpeta privadas."],
        ),
    ):
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
