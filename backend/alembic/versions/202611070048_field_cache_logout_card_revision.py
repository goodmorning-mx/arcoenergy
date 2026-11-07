"""Record account-scoped offline snapshot cleanup on logout.

Revision ID: 202611070048
Revises: 202611070047
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070048"
down_revision = "202611070047"
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
        bind, history, "US-14", "Iteración 37 · limpieza de datos privados en PWA · 2026-11-07",
        ["Al cerrar sesión en la PWA se eliminan de IndexedDB las instantáneas de órdenes, inventario y movimientos asociadas a la cuenta.",
         "La limpieza no descarta operaciones de campo que aún esperan sincronizarse."],
        ["La política de retención y borrado remoto de los dispositivos usados por el equipo debe validarse con ArcoEnergy."],
    )
    _append_revision(
        bind, history, "US-40", "Iteración 37 · limpieza de caché de campo al salir · 2026-11-07",
        ["Las vistas operativas guardadas localmente se borran al cerrar sesión para reducir la exposición en dispositivos compartidos.",
         "Las colas pendientes quedan asociadas a la cuenta y se conservan para sincronizarse cuando vuelva a iniciar sesión esa misma cuenta."],
        ["Validar el comportamiento y retención de IndexedDB en teléfonos reales del equipo."],
    )


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    for iteration in (
        "Iteración 37 · limpieza de datos privados en PWA · 2026-11-07",
        "Iteración 37 · limpieza de caché de campo al salir · 2026-11-07",
    ):
        op.execute(sa.delete(history).where(
            history.c.iteration == iteration,
            history.c.recorded_by == "system:implementation-iteration",
        ))
