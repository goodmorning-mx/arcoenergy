"""Record client identity provisioning and portal scope for US-14.

Revision ID: 202611110135
Revises: 202611110134
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110135"
down_revision = "202611110134"
branch_labels = None
depends_on = None

ITERATION = "Iteración 123 · alta de cuentas cliente vinculadas a cartera · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-14").order_by(history.c.version.desc())
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
            "El rol cliente solo se crea o asigna cuando el correo de la cuenta coincide con una ficha existente de la cartera.",
            "El portal limita propuestas, instalaciones y pagos a fichas con el correo autenticado y omite notas y referencias privadas internas.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Falta validar el alta y acceso con identidades reales creadas por administración en DEV.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
