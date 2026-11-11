"""Append the current DEV anonymous read-route audit to US-14.

Revision ID: 202611110129
Revises: 202611110128
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110129"
down_revision = "202611110128"
branch_labels = None
depends_on = None

ITERATION = "Iteración 117 · auditoría anónima API DEV · 2026-11-11"
OPENAPI_URL = "https://api.dev.arcoenergy.goodmorning.mx/openapi.json"
OPENAPI_SHA256 = "8c73e79b4fc9c5fb1e71ec2017b1098789c4406ae41598ad9d85699dc4425589"
API_COMMIT = "df4043e782e4504c3fb29c8dcd50e9cc125d0f4f"
SCHEMA_REVISION = "202611110128"
PRIVATE_GET_COUNT = 34


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-14").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return

    revised = dict(original)
    artifacts = list((original["source_artifact"] or {}).get("artifacts", []))
    artifact_index = len(artifacts)
    artifacts.append({
        "artifact_type": "Live DEV OpenAPI document",
        "reference": OPENAPI_URL,
        "channel": "ArcoEnergy DEV API",
        "location": f"Commit {API_COMMIT}; schema {SCHEMA_REVISION}; fetched 2026-11-11",
        "sha256": OPENAPI_SHA256,
    })
    links = list(original["source_links"] or [])
    links.append({
        "artifact_index": artifact_index,
        "relation": "validation",
        "location": f"34/34 GET operations under /v1 returned HTTP 401 without credentials",
    })
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "source_reference": f"{original['source_reference']}; OpenAPI DEV {API_COMMIT}/{SCHEMA_REVISION}",
        "source_artifact": {"artifacts": artifacts},
        "source_links": links,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "En la revisión de DEV, las 34 rutas GET de /v1 enumeradas por OpenAPI devuelven HTTP 401 sin credenciales, incluso para rutas con parámetros de recurso.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La prueba anónima no verifica permisos por rol, organización, cliente o campo; faltan cuentas reales autorizadas para probar esos alcances.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
