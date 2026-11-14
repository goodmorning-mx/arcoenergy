"""Record live DEV login, refresh rotation and logout evidence append-only.

Revision ID: 202611140153
Revises: 202611140152
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611140153"
down_revision = "202611140152"
branch_labels = None
depends_on = None

ITERATION = "Iteración 151 · verificación viva de sesión persistente · 2026-11-14"
UPDATES = {
    "US-14": (
        "En DEV se verificó una autenticación real de la cuenta de bootstrap configurada: inicio de sesión correcto, refresh rotado, identidad validada y cierre de sesión que revoca el token; AUTH_REFRESH_DAYS es 36,500. Las tres cuentas solicitadas permanecen activas con roles administrador, marketing y contador. No se imprimieron ni guardaron credenciales o tokens.",
        "La sesión evita vencimientos operativos mediante refresh renovable de hasta 36,500 días; cerrar sesión, restablecer contraseña o desactivar usuario la revoca. Falta validar renovación y permisos en teléfonos reales de instaladores/clientes y cotejar el aislamiento de datos con usuarios de esos roles.",
    ),
    "US-40": (
        "La configuración desplegada de DEV usa refresh renovable por 36,500 días. Una prueba de runtime inició sesión con la cuenta de bootstrap, rotó el refresh, validó la identidad y revocó la sesión al cerrar; Chrome CI cubre restauración del estado autenticado tras recargar y el reintento de una acción de campo.",
        "La identidad usada en la prueba de runtime es la cuenta de bootstrap administrativa; faltan cuentas reales de instalador/cliente y validación de renovación/reintento en teléfonos físicos y periodos largos en segundo plano.",
    ),
    "US-42": (
        "Iteración 151 agrega evidencia append-only de login, rotación de refresh, identidad y logout verificados en DEV, conservando el relato fuente original de US-14, US-40 y US-42.",
        "Falta el cotejo humano de transcripciones/reconstrucciones de storycards y la validación con stakeholders de su interpretación.",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criterion, unresolved) in UPDATES.items():
        latest = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if latest is None:
            continue
        acceptance = list(latest["acceptance_criteria"] or [])
        questions = list(latest["unresolved_questions"] or [])
        if criterion not in acceptance:
            acceptance.append(criterion)
        if unresolved not in questions:
            questions.append(unresolved)
        revised = dict(latest)
        revised.update({
            "id": str(uuid4()), "version": latest["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": acceptance, "unresolved_questions": questions,
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    # Story history is append-only; rollback is forward-only.
    pass
