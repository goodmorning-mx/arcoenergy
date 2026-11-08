"""Add precise source excerpts and current implementation state to history cards.

Revision ID: 202611080066
Revises: 202611080065
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611080066"
down_revision = "202611080065"
branch_labels = None
depends_on = None

ITERATION = "Iteración 55 · trazabilidad de fuentes y registro de history cards · 2026-11-08"
SOURCE = "docs/discovery/sources/owner-product-brief-2026-11-06.md"

REVISIONS = {
    "US-39": {
        "normalized_story": "Como administrador, quiero que el CRM de escritorio sea el panel administrativo central para gestionar el sistema empresarial.",
        "excerpt": "el CRM es el sistema de administracion es un panel dashboard para las computadoras y es el panel admin de todo.",
        "location": "Distribución funcional de portales, primer mensaje citado; oración sobre CRM.",
        "criteria": ["La tarjeta conserva el mensaje literal completo y enlaza la interpretación CRM al fragmento exacto de la fuente."],
    },
    "US-40": {
        "normalized_story": "Como integrante del equipo de campo, quiero usar una PWA móvil operativa para ejecutar las acciones de mi trabajo.",
        "excerpt": "el PWA es una aplicacion mobile para las personas de campo y ademas un cliente para los empleados. donde se van a ejecutar ciertas mas que nada acciones porque es operativa.",
        "location": "Distribución funcional de portales, primer mensaje citado; oraciones sobre PWA.",
        "criteria": ["La tarjeta conserva el mensaje literal completo y enlaza la interpretación PWA al fragmento exacto de la fuente."],
    },
    "US-41": {
        "normalized_story": "Como prospecto, quiero conversar con un agente de IA en la web para recibir una cotización de paneles solares.",
        "excerpt": "la web es una web donde vamos a cotizar por IA agentica; donde hablamos con una IA para que nos cotice paneles solares. a su vez este proyecto va a usar el MCP server y otros modulos de goodmorning-factry por lo que tambien ve a leerlos en nuestro github.",
        "location": "Distribución funcional de portales, primer mensaje citado; oraciones sobre web, agente y módulos.",
        "criteria": ["La tarjeta conserva el mensaje literal completo y enlaza la interpretación web/agente al fragmento exacto de la fuente."],
    },
    "US-42": {
        "normalized_story": "Como dueño del producto, quiero que los hallazgos se registren como history cards versionadas, con relatos literales preservados y cambios append-only integrados en dev.",
        "excerpt": None,
        "location": "Diseño y proceso por iteraciones, mensajes citados del dueño del producto.",
        "criteria": [
            "ae_history_cards conserva las versiones de las 42 tarjetas recuperadas y reconstruidas con su relato fuente.",
            "El API permite consultar tarjetas y añadir una nueva versión append-only.",
            "El CRM ofrece la vista de history cards y requiere el relato literal para registrar una versión.",
            "Esta revisión no modifica source_literal ni las versiones anteriores.",
        ],
        "questions": [
            "Las tarjetas reconstruidas US-1–US-34 y las transcripciones ASR todavía deben cotejarse con sus autores; esta corrección de procedencia no constituye validación del stakeholder.",
            "Los artefactos sensibles requieren almacenamiento privado autorizado y una política de acceso y retención acordada.",
        ],
    },
}


def upgrade() -> None:
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, update in REVISIONS.items():
        original = bind.execute(
            sa.select(history)
            .where(history.c.story_id == story_id)
            .order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "normalized_story": update["normalized_story"],
            "source_confidence": "verbatim_excerpt",
            "source_links": [{
                "artifact_index": 0,
                "relation": "verbatim_excerpt" if update["excerpt"] else "verbatim_source_reference",
                "location": update["location"],
                **({"excerpt": update["excerpt"]} if update["excerpt"] else {}),
            }],
            "acceptance_criteria": [*original["acceptance_criteria"], *update["criteria"]],
            "unresolved_questions": [
                *original["unresolved_questions"],
                *update.get("questions", []),
            ],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table(
        "ae_history_cards",
        sa.column("iteration", sa.String()),
        sa.column("recorded_by", sa.String()),
    )
    op.execute(
        sa.delete(history).where(
            history.c.iteration == ITERATION,
            history.c.recorded_by == "system:implementation-iteration",
        )
    )
