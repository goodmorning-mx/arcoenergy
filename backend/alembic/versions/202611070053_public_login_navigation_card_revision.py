"""Expose the production CRM login from the public site navigation.

Revision ID: 202611070053
Revises: 202611070052
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070053"
down_revision = "202611070052"
branch_labels = None
depends_on = None

ITERATION = "Iteración 42 · acceso visible desde el sitio público · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-14": (
            ["El sitio público muestra el acceso al CRM y el formulario de autenticación está disponible en /login y /crm/login."],
            ["Validar con usuarios del negocio si el inicio debe recordar una ruta protegida solicitada antes de autenticarse."],
        ),
        "US-39": (
            ["La cabecera pública ofrece un acceso visible a administración que dirige a /login, además del enlace que permanece en el pie de página."],
            ["Las vistas administrativas continúan exigiendo credenciales válidas y privilegios asignados."],
        ),
        "US-40": (
            ["La vista de acceso CRM conserva un vínculo directo al acceso móvil /app/login para el personal y los clientes autorizados."],
            ["Falta verificar la navegación completa con cuentas reales de instalador y cliente cuando se carguen."],
        ),
    }
    for story_id, (criteria, questions) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
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
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
