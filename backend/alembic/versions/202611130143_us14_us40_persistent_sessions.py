"""Record persistent, renewable sessions for US-14 and US-40.

Revision ID: 202611130143
Revises: 202611120142
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130143"
down_revision = "202611120142"
branch_labels = None
depends_on = None
ITERATION = "Iteración 139 · sesión persistente y renovación transparente · 2026-11-13"
CARD_UPDATES = {
    "US-14": (
        "CRM conserva la sesión entre recargas y renueva el token de acceso y su refresh token rotatorio antes del vencimiento. "
        "La sesión se comparte entre pestañas del mismo origen, y cerrar sesión elimina el estado local e invalida el refresh token.",
        "La renovación se probó en Chrome para CRM con refresh mock rotatorio, recarga, error temporal y logout. La sesión inactiva por más de 30 días puede requerir nuevo acceso; validar la política de inactividad con administración.",
    ),
    "US-40": (
        "PWA conserva la sesión entre recargas y renueva el token de acceso y su refresh token rotatorio antes del vencimiento. "
        "Una falla temporal de red conserva la sesión y reintenta; cerrar sesión elimina el estado local e invalida el refresh token.",
        "La renovación se probó en Chrome para PWA con refresh mock rotatorio, recarga, error temporal y logout. La sesión inactiva por más de 30 días puede requerir nuevo acceso; validar la política de inactividad y teléfonos de campo.",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criterion, unresolved) in CARD_UPDATES.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], criterion],
            "unresolved_questions": [*original["unresolved_questions"], unresolved],
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
