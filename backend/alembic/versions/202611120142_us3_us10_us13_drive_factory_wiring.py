"""Record optional Factory-managed Google Drive credentials for ArcoEnergy.

Revision ID: 202611120142
Revises: 202611120141
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611120142"
down_revision = "202611120141"
branch_labels = None
depends_on = None
ITERATION = "Iteración 130 · preparación segura de credenciales Drive en Factory · 2026-11-12"

CARD_UPDATES = {
    "US-3": (
        "Factory DEV ahora declara el ID de carpeta privada y un secreto opcional para la cuenta de servicio de Drive. "
        "Esto prepara la conexión de cotizaciones sin almacenar la credencial en Git.",
        "Configurar el ID de carpeta aprobado y el secreto de servicio; después comprobar carga/lectura de un PDF y compartirlo desde un dispositivo real.",
    ),
    "US-10": (
        "Los comprobantes de gastos reutilizan la configuración privada de Drive declarada para el API; la credencial opcional no bloquea despliegues DEV.",
        "Configurar la carpeta y el secreto aprobados; confirmar carga, acceso y reintento de un comprobante real.",
    ),
    "US-13": (
        "Factory DEV puede entregar al API la credencial de servicio de Google Drive como secreto opcional y no imprime su valor. "
        "El manifiesto mantiene vacía la carpeta hasta que administración indique la carpeta privada.",
        "Faltan el secreto de cuenta de servicio y el ID de carpeta; no se ha confirmado una exportación empresarial ni un respaldo JSON real en Drive.",
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
        acceptance = list(original["acceptance_criteria"] or [])
        if criterion not in acceptance:
            acceptance.append(criterion)
        questions = list(original["unresolved_questions"] or [])
        if unresolved not in questions:
            questions.append(unresolved)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": acceptance,
            "unresolved_questions": questions,
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
