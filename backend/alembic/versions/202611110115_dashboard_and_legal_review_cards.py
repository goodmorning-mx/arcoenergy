"""Record dashboard verification and explicit legal gates for US-5/6/19.

Revision ID: 202611110115
Revises: 202611110114
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110115"
down_revision = "202611110114"
branch_labels = None
depends_on = None

ITERATION = "Iteración 103 · dashboard y dependencias legales · 2026-11-11"
REVISIONS = {
    "US-19": {
        "acceptance_criteria": [
            "El dashboard CRM muestra una gráfica de movimientos de almacén de siete días y un resumen visual de disponibilidad, mínimos y agotados.",
            "El dashboard muestra cartera vencida/próxima y saldos de cuentas según el permiso de cada rol.",
        ],
        "unresolved_questions": [
            "Contabilidad/administración debe validar umbrales de oportunidad, métricas del dashboard y el alcance de la gráfica financiera.",
        ],
    },
    "US-5": {
        "acceptance_criteria": [
            "No generar contratos ni pagarés hasta que la empresa entregue y apruebe las plantillas legales y los campos requeridos.",
            "No extraer ni almacenar INE del titular o responsable solidario hasta acordar finalidad, consentimiento, acceso y retención.",
        ],
        "unresolved_questions": [
            "Pendiente: plantillas vigentes de contrato/pagaré y sus reglas de contado/financiamiento.",
            "Pendiente: consentimiento informado, mecanismo de revisión de identidad, permisos y periodo de retención de INE.",
        ],
    },
    "US-6": {
        "acceptance_criteria": [
            "No activar firma electrónica o análisis facial hasta aprobar proveedor, flujo de consentimiento, verificación y alternativa física.",
        ],
        "unresolved_questions": [
            "Pendiente: decisión legal sobre validez de firma y biometría, proveedor autorizado, consentimiento y conservación de evidencia.",
        ],
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, additions in REVISIONS.items():
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
            "acceptance_criteria": [*original["acceptance_criteria"], *additions["acceptance_criteria"]],
            "unresolved_questions": [*original["unresolved_questions"], *additions["unresolved_questions"]],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
