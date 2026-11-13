"""Record the no-idle-expiry session policy for US-14 and US-40.

Revision ID: 202611130145
Revises: 202611130144
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130145"
down_revision = "202611130144"
branch_labels = None
depends_on = None
ITERATION = "Iteración 143 · sesión sin vencimiento operativo · 2026-11-13"
CARD_UPDATES = {
    "US-14": (
        "La sesión del CRM no exige volver a iniciar sesión por inactividad en el uso operativo: el refresh token se rota y su vigencia se renueva por 36,500 días (100 años) en cada renovación. "
        "Cerrar sesión, restablecer la contraseña o desactivar la cuenta revoca el acceso.",
        "La política de 100 años elimina el vencimiento por inactividad en el horizonte operativo solicitado. Chrome CI verifica la rotación, restauración y logout; siguen pendientes validar cuentas reales y aislamiento por rol.",
    ),
    "US-40": (
        "La sesión de PWA no exige volver a iniciar sesión por inactividad en el uso operativo: el refresh token se rota y su vigencia se renueva por 36,500 días (100 años) en cada renovación. "
        "Cerrar sesión, restablecer la contraseña o desactivar la cuenta revoca el acceso.",
        "La política de 100 años elimina el vencimiento por inactividad en el horizonte operativo solicitado. Chrome CI verifica la rotación, restauración y logout; falta validarla también en teléfonos físicos con cuentas reales de campo.",
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
        unresolved_questions = [
            question for question in original["unresolved_questions"]
            if "30 días" not in question
        ]
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], criterion],
            "unresolved_questions": [*unresolved_questions, unresolved],
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
