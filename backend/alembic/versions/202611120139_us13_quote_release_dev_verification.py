"""Record DEV release evidence for the PWA quote and backup cards.

Revision ID: 202611120139
Revises: 202611120138
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611120139"
down_revision = "202611120138"
branch_labels = None
depends_on = None
ITERATION = "Iteración 127 · despliegue DEV de cotizador PWA y esquema · 2026-11-12"
REVISIONS = {
    "US-1": (
        ["La revisión de cotizador PWA quedó incluida en el código de DEV desplegado por Factory; el flujo autenticado de selección aún requiere validación con cuentas comerciales reales."],
        ["Falta recorrer la selección y emisión con una cartera real en DEV y confirmar el catálogo aprobado."],
    ),
    "US-3": (
        ["Factory desplegó los cinco servicios DEV después de integrar la revisión del cotizador; esto acredita el despliegue de la aplicación, no una carga del PDF a Drive."],
        ["Drive empresarial continúa sin credenciales/carpeta configuradas y falta validar la entrega por WhatsApp con clientes reales."],
    ),
    "US-13": (
        ["Factory run 43146112522 terminó con éxito: los cinco servicios DEV finalizaron, la base viva confirmó el esquema 202611120138 y el respaldo externo de PostgreSQL quedó verificado."],
        ["La verificación de PostgreSQL no acredita una carga empresarial JSON en Google Drive; faltan configuración privada, carga real, retención y prueba de restauración."],
    ),
}

def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))

def downgrade() -> None:
    pass
