"""Record date-filtered account cash flow reporting iteration.

Revision ID: 202611070047
Revises: 202611070046
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070047"
down_revision = "202611070046"
branch_labels = None
depends_on = None


def _append_revision(bind, history, story_id, iteration, criteria, questions):
    original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": iteration,
        "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
        "unresolved_questions": [*original["unresolved_questions"], *questions],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    _append_revision(
        bind, history, "US-19", "Iteración 36 · flujo de caja por periodo · 2026-11-07",
        [
            "CRM muestra para el rango consultado saldos al inicio y cierre, aperturas de cuentas en el periodo, entradas y salidas registradas por fecha de captura.",
            "El resumen se desglosa por cuenta activa y muestra datos únicamente a identidades con permiso de lectura de cuentas.",
            "El reporte distingue movimientos capturados de proyecciones y conciliación bancaria.",
        ],
        [
            "Validar con contabilidad el tratamiento de traspasos entre cuentas y de saldos de cuentas inactivas.",
            "La vista no concilia contra estados bancarios ni proyecta movimientos futuros.",
        ],
    )
    _append_revision(
        bind, history, "US-18", "Iteración 36 · flujo de caja por cuenta · 2026-11-07",
        ["El reporte operativo presenta por cuenta activa el saldo inicial del rango, movimientos de entrada y salida y saldo calculado al cierre."],
        ["Falta conciliar los movimientos registrados con estados de cuenta bancarios y validar traspasos internos."],
    )


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 36 · flujo de caja por periodo · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 36 · flujo de caja por cuenta · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
