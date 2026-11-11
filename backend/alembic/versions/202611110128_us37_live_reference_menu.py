"""Append live public menu evidence to US-37 without claiming UI parity.

Revision ID: 202611110128
Revises: 202611110127
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110128"
down_revision = "202611110127"
branch_labels = None
depends_on = None

ITERATION = "Iteración 116 · menú vivo de referencia US-37 · 2026-11-11"
REFERENCE_URL = "https://arco-energy.base44.app/"
MENU_BUNDLE_URL = "https://arco-energy.base44.app/assets/index-R4F2cERi.js"
MENU_BUNDLE_SHA256 = "5034ad69f06abeca357fa722128cf4f1d31e6d5c7ffcf5b64a2b4aa6c03bddfc"
MENU_ITEMS = [
    ("Dashboard", "/"),
    ("Inventario", "/inventory"),
    ("Entradas", "/entries"),
    ("Salidas", "/exits"),
    ("Kardex", "/kardex"),
    ("Escáner", "/scanner"),
    ("Reportes", "/reports"),
    ("Proveedores", "/suppliers"),
    ("Proyectos", "/projects"),
    ("Usuarios", "/users"),
    ("Configuración", "/settings"),
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-37").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return

    revised = dict(original)
    artifacts = list((original["source_artifact"] or {}).get("artifacts", []))
    artifact_index = len(artifacts)
    artifacts.append({
        "artifact_type": "Public app JavaScript menu bundle",
        "reference": MENU_BUNDLE_URL,
        "channel": "Public website source asset",
        "location": "Active navigation declarations; fetched 2026-11-11",
        "sha256": MENU_BUNDLE_SHA256,
    })
    links = list(original["source_links"] or [])
    links.append({
        "artifact_index": artifact_index,
        "relation": "validation",
        "location": "MENU_ITEMS; public root and bundle each returned HTTP 200",
    })
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "source_reference": f"{original['source_reference']}; validación pública: {REFERENCE_URL}",
        "source_artifact": {"artifacts": artifacts},
        "source_links": links,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "El menú del sitio público de referencia expone Dashboard, Inventario, Entradas, Salidas, Kardex, Escáner, Reportes, Proveedores, Proyectos, Usuarios y Configuración, en rutas observadas en el bundle del 2026-11-11.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La evidencia pública confirma etiquetas y rutas declaradas, no vistas renderizadas, datos ni operaciones autenticadas. Para cotejo de comportamiento/visual se necesita acceso autorizado a las pantallas de César o capturas navegables.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
