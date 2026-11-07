"""Add reviewed work order material issue flow and its role grant.

Revision ID: 202611060044
Revises: 202611060043
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611060044"
down_revision = "202611060043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    memberships = sa.Table("gm_auth_memberships", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(sa.select(memberships.c.user_id, memberships.c.organization_id,
                                      memberships.c.roles, memberships.c.permissions)).mappings():
        roles = {str(role).strip().lower() for role in (row["roles"] or [])}
        if roles & {"admin", "administrador", "contador", "finanzas"}:
            permissions = sorted(set(row["permissions"] or []) | {"inventory:issue"})
            bind.execute(sa.update(memberships).where(
                memberships.c.user_id == row["user_id"],
                memberships.c.organization_id == row["organization_id"],
            ).values(permissions=permissions))

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-25")
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": "Iteración 33 · revisión y salida física desde solicitud · 2026-11-07",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "CRM permite adjuntar temporalmente una foto o PDF de solicitud y revisar manualmente las cantidades antes de confirmar la salida física.",
            "La salida confirmada descuenta existencia disponible una sola vez, queda ligada a la orden y al material solicitado y se refleja en el kardex.",
            "Los artículos emitidos pueden devolverse o registrarse como dañados contra la salida original, conservando su trazabilidad.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "OCR y extracción automática de solicitudes manuscritas no están disponibles; validar formato y campos con almacén.",
            "La imagen/PDF solo se previsualiza localmente en CRM y no se conserva ni sincroniza a Drive; falta definir y configurar retención documental.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 33 · revisión y salida física desde solicitud · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
    # Preserve grants: memberships may have been assigned the permission explicitly after upgrade.
