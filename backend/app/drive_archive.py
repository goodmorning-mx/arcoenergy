"""Private, on-demand export of ArcoEnergy business data to Google Drive."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import json

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.config import get_settings
from app.drive_storage import save_private_file
from app.models import Base
from gm_auth.models import memberships, users


# These rows contain device credentials or transient replay payloads. Business
# records and their durable audit history are included in the archive.
EXCLUDED_TABLES = {
    "ae_push_subscriptions": "Claves y endpoints privados de notificación por dispositivo.",
    "ae_offline_operations": "Cola técnica de idempotencia y repetición de solicitudes sincronizadas.",
    "ae_integrations": "Metadatos de conexión que podrían incluir configuración sensible de proveedores.",
}
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


def _json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def build_business_snapshot(db: Session, team_members_override: list[dict] | None = None) -> tuple[bytes, int, str]:
    """Serialize a repeatable-read snapshot, excluding transient device secrets."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))

    tables: dict[str, list[dict]] = {}
    row_count = 0
    for table in sorted(Base.metadata.sorted_tables, key=lambda item: item.name):
        if table.name in EXCLUDED_TABLES:
            continue
        rows = db.execute(select(table)).mappings().all()
        tables[table.name] = [
            {column.name: _json_value(row[column.name]) for column in table.columns}
            for row in rows
        ]
        row_count += len(rows)

    if team_members_override is None:
        with auth_service.engine.connect() as connection:
            team = connection.execute(
                select(users.c.id, users.c.email, users.c.name, users.c.is_active,
                       memberships.c.roles, memberships.c.permissions)
                .join(memberships, memberships.c.user_id == users.c.id)
                .where(memberships.c.organization_id == get_settings().organization_id)
                .order_by(users.c.email)
            ).mappings().all()
        team_members = [{
            "id": row["id"], "email": row["email"], "name": row["name"],
            "is_active": row["is_active"], "roles": sorted(row["roles"] or []),
            "permissions": sorted(row["permissions"] or []),
        } for row in team]
    else:
        team_members = team_members_override
    row_count += len(team_members)

    generated_at = datetime.now(timezone.utc)
    payload = {
        "format": "arcoenergy-business-data-v1",
        "generated_at": generated_at.isoformat(),
        "organization_id": get_settings().organization_id,
        "consistency": {
            "product_tables": "repeatable_read" if db.get_bind().dialect.name == "postgresql" else "single_database_transaction",
            "team_profiles": "separate_auth_database_read",
        },
        "included_tables": sorted(tables),
        "excluded_tables": EXCLUDED_TABLES,
        "authentication": {
            "included": "organization team profile, roles and permissions",
            "excluded": "password hashes, session tokens and authentication secrets",
        },
        "record_count": row_count,
        "team_members": team_members,
        "tables": tables,
    }
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(content) > MAX_ARCHIVE_BYTES:
        raise ValueError("El archivo supera el límite de exportación de 64 MB.")
    filename = f"arcoenergy-datos-{generated_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    return content, row_count, filename


def archive_business_snapshot(db: Session) -> dict:
    content, row_count, filename = build_business_snapshot(db)
    file_id = save_private_file(
        filename=filename,
        content=content,
        content_type="application/json",
    )
    return {"filename": filename, "file_id": file_id, "bytes": len(content), "record_count": row_count}
