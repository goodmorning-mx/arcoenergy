"""Register the inventory module reference as US-44.

Revision ID: 202611170158
Revises: 202611170157
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611170158"
down_revision = "202611170157"
branch_labels = None
depends_on = None

ITERATION = "Iteración 156 · funcionalidades del módulo de inventario · 2026-11-17"
SOURCE_LITERAL = "Mira ahora vamos a trabajar por modulos; entonces vas a agregar historycards que yo mismo fui agregando; entonces la siguiente storycard que necesito es que dentro del modulo de inventario dejes todas estas funcionalidades que ya tiene el sistema de inventario."
IMAGE_PATH = "docs/discovery/sources/inventory-module-reference.png"
IMAGE_SHA256 = "a80989d859ee17d3ce3acbef07180208bc6f49cbdf3870ec5373018b6a53d2ec"
NORMALIZED_STORY = (
    "Como responsable del inventario de Arco Energy, quiero conservar y disponer desde el módulo de inventario "
    "las funciones y el resumen operativo que aparecen en la captura de referencia, para controlar existencias, "
    "movimientos y alertas desde un solo espacio."
)
ACCEPTANCE_CRITERIA = (
    "El dashboard muestra productos totales, artículos con stock bajo, entradas de hoy, salidas de hoy, valor del inventario y movimientos de los últimos siete días.",
    "Una gráfica compara entradas y salidas durante los últimos siete días.",
    "El panel de alertas de stock bajo identifica cada producto y muestra la existencia actual frente al mínimo configurado; las cantidades críticas se distinguen visualmente.",
    "Los movimientos recientes muestran artículo, tipo o folio del movimiento, cantidad y fecha.",
    "La navegación del portal conserva accesos a Dashboard, Inventario, Entradas, Salidas, Kardex, Escáner, Reportes, Proveedores, Proyectos, Usuarios y Configuración, conforme a los permisos de cada rol.",
    "Los resúmenes, alertas y movimientos representan los registros existentes y no usan datos de demostración.",
)
UNRESOLVED_QUESTIONS = (
    "Confirmar con el responsable de inventario las fórmulas y período exactos de cada indicador, la valuación del almacén y los umbrales de stock bajo.",
    "Confirmar qué roles deben consultar costos, proveedores, proyectos, usuarios y configuración desde este menú.",
    "El autor nominal de esta solicitud no se identifica en el mensaje; no atribuirlo a partir del nombre visible en la captura.",
)
LINKED_CARDS = ["US-19", "US-20", "US-26", "US-27", "US-28", "US-29", "US-30", "US-32"]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    exists = bind.execute(sa.select(history.c.id).where(history.c.story_id == "US-44").limit(1)).first()
    if exists:
        return
    artifact = {
        "artifacts": [
            {
                "artifact_type": "mensaje de conversación",
                "reference": "Chat del proyecto Arco Energy · solicitud del módulo de inventario",
                "channel": "ChatGPT",
                "location": "Mensaje del usuario del 2026-11-17",
                "sha256": None,
            },
            {
                "artifact_type": "captura de pantalla de referencia",
                "reference": IMAGE_PATH,
                "channel": "Imagen compartida por el usuario",
                "location": "Vista completa del dashboard y navegación de inventario",
                "sha256": IMAGE_SHA256,
            },
        ]
    }
    links = [
        {"artifact_index": 0, "relation": "literal", "location": "Solicitud literal de US-44"},
        {"artifact_index": 1, "relation": "inference", "location": "Elementos visibles en el dashboard de referencia"},
    ]
    bind.execute(history.insert().values(
        id=str(uuid4()), story_id="US-44", version=1, iteration=ITERATION,
        stakeholder="Equipo Arco Energy", requested_by="Por identificar",
        source_literal=SOURCE_LITERAL, source_type="Conversación e imagen",
        source_reference=f"docs/discovery/sources/inventory-module-reference.md · {IMAGE_PATH}",
        source_artifact=artifact, source_language="es",
        source_attribution="Usuario Arco Energy (autor nominal por identificar)",
        source_occurred_at="2026-11-17", source_confidence="needs_validation",
        source_links=links, normalized_story=NORMALIZED_STORY,
        acceptance_criteria=list(ACCEPTANCE_CRITERIA),
        unresolved_questions=list(UNRESOLVED_QUESTIONS), linked_cards=LINKED_CARDS,
        recorded_by="system:discovery-iteration-156", created_at=datetime.now(timezone.utc),
    ))


def downgrade() -> None:
    # Story cards are append-only discovery records and remain on rollback.
    pass
