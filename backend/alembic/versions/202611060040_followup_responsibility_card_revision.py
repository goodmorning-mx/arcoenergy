"""Assign follow-ups to an active commercial team member.

Revision ID: 202611060040
Revises: 202611060039
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060040"
down_revision = "202611060039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    followup_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_followups")}
    if "assigned_to" not in followup_columns:
        op.add_column("ae_followups", sa.Column("assigned_to", sa.String(length=180), nullable=False, server_default=""))
    followups = sa.table("ae_followups", sa.column("created_by", sa.String()), sa.column("assigned_to", sa.String()))
    op.execute(followups.update().where(followups.c.assigned_to == "").values(assigned_to=followups.c.created_by))

    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-4").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 29 · responsabilidad de seguimientos · 2026-11-06",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Cada seguimiento tiene un responsable miembro activo del equipo con permiso comercial; por defecto es quien lo programa y administración puede asignar a otra persona autorizada.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Las alertas se muestran dentro del CRM; correo, push y mensajería automática requieren definir canal y proveedor.",
        ],
        "linked_cards": sorted(set([*original["linked_cards"], "US-14"])),
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 29 · responsabilidad de seguimientos · 2026-11-06",
        history.c.recorded_by == "system:implementation-iteration",
    ))
    followup_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_followups")}
    if "assigned_to" in followup_columns:
        op.drop_column("ae_followups", "assigned_to")
