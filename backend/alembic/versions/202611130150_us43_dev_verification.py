"""Record deployed CRM agent operation verification as an append-only iteration.

Revision ID: 202611130150
Revises: 202611130149
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611130150"
down_revision = "202611130149"
branch_labels = None
depends_on = None

ITERATION = "Iteración 148 · verificación DEV del agente CRM · 2026-11-13"
UPDATES = {
    "US-43": (
        "En DEV, el asistente CRM programa seguimientos con una vista previa legible y confirmación explícita; el servidor vuelve a comprobar permiso vigente y evita duplicados. La versión fdf7a4de3d9c06a4a1d0cb3dbef8194fa42bdf4d respondió con salud OK y schema 202611130149; CI verificó Docker, OCR, render de PWA/CRM, sesión persistente y login PWA offline.",
        "Falta que los stakeholders prioricen las siguientes operaciones del agente y aprueben el alcance de datos que procesa el proveedor del modelo.",
    ),
    "US-42": (
        "La auditoría de schema 202611130149 registra 43 tarjetas y 349 versiones append-only; US-43 v2 conserva el relato fuente literal no vacío. Esta verificación queda registrada en Iteración 148 sin editar versiones anteriores.",
        "Falta el cotejo humano de reconstrucciones/transcripciones y definir retención de fuentes sensibles.",
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
    # Preserve the append-only story history; rollback is forward-only.
    pass
