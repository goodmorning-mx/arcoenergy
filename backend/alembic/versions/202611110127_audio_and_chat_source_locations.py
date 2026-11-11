"""Append source-accurate locations for ASR and WhatsApp history cards.

Revision ID: 202611110127
Revises: 202611110126
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110127"
down_revision = "202611110126"
branch_labels = None
depends_on = None

ITERATION = "Iteración 115 · ubicaciones literales de fuentes · 2026-11-11"
TRANSCRIPT = "docs/discovery/sources/contador-whatsapp-audio-transcripts-2026-11-02.md"
MARIO = "docs/discovery/sources/mario-groso-whatsapp-2026-11-05.md"

AUDIO_CARDS = {
    "US-33": {
        "source_reference": f"{TRANSCRIPT}; WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg; 00:00–00:38",
        "source_attribution": "Contador remitente no identificado; transcripción ASR Faster-Whisper small",
        "source_artifact": {"artifacts": [
            {"artifact_type": "WhatsApp voice note OGG", "reference": "/home/goodmorning/Downloads/WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg", "channel": "WhatsApp", "location": "00:00–00:38", "sha256": "e2582c5049ad54cfe0d7b48308661c1afa0f75899f2ba7de807c380f49707c04"},
            {"artifact_type": "ASR transcript", "reference": TRANSCRIPT, "channel": "Faster-Whisper small · es · CPU/int8", "location": "Clip 4.16.19 PM, líneas 22–38", "sha256": None},
        ]},
        "source_links": [
            {"artifact_index": 0, "relation": "transcription", "location": "WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg, 00:00–00:38"},
            {"artifact_index": 1, "relation": "transcription", "location": "Clip 4.16.19 PM, marcas 00:00–00:38"},
        ],
        "unresolved": "El ASR contiene la frase dudosa «entradas alimentarios»; confirmar con el stakeholder antes de corregirla o tratarla como cita literal validada.",
    },
    "US-34": {
        "source_reference": f"{TRANSCRIPT}; WhatsApp Ptt 2026-11-02 at 4.15.39 PM.ogg (00:00–00:23) y 4.16.19 PM.ogg (00:00–00:38)",
        "source_attribution": "Contador remitente no identificado; transcripción ASR Faster-Whisper small",
        "source_artifact": {"artifacts": [
            {"artifact_type": "WhatsApp voice note OGG", "reference": "/home/goodmorning/Downloads/WhatsApp Ptt 2026-11-02 at 4.15.39 PM.ogg", "channel": "WhatsApp", "location": "00:00–00:23", "sha256": "a8a324099050cb5a25c72e49a670bf294a815702cdf448a8d60443d309315080"},
            {"artifact_type": "WhatsApp voice note OGG", "reference": "/home/goodmorning/Downloads/WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg", "channel": "WhatsApp", "location": "00:00–00:38", "sha256": "e2582c5049ad54cfe0d7b48308661c1afa0f75899f2ba7de807c380f49707c04"},
            {"artifact_type": "ASR transcript", "reference": TRANSCRIPT, "channel": "Faster-Whisper small · es · CPU/int8", "location": "Clips 4.15.39 PM y 4.16.19 PM", "sha256": None},
        ]},
        "source_links": [
            {"artifact_index": 0, "relation": "transcription", "location": "WhatsApp Ptt 2026-11-02 at 4.15.39 PM.ogg, 00:00–00:23"},
            {"artifact_index": 1, "relation": "transcription", "location": "WhatsApp Ptt 2026-11-02 at 4.16.19 PM.ogg, 00:00–00:38"},
            {"artifact_index": 2, "relation": "transcription", "location": "Clip 4.15.39 PM, 00:00–00:23; clip 4.16.19 PM, 00:00–00:38"},
        ],
        "unresolved": "La transcripción combina dos audios y el primero termina incompleto. El remitente debe validar la atribución y el contenido reconocido antes de considerarlo relato literal confirmado.",
    },
}

MARIO_LINKS = [
    {"artifact_index": 0, "relation": "literal", "location": "Mensaje 12:54 p.m., pregunta sobre datos contables"},
    {"artifact_index": 0, "relation": "literal", "location": "Mensaje 12:55 p.m., relación entre afectaciones"},
    {"artifact_index": 0, "relation": "literal", "location": "Mensaje 12:58 p.m., ventas, ventas a crédito y compras de material"},
    {"artifact_index": 0, "relation": "literal", "location": "Mensaje 1:01 p.m., afectaciones en paralelo"},
    {"artifact_index": 0, "relation": "literal", "location": "Mensaje 1:01 p.m., orden de trabajo y salida de almacén"},
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)

    updates = {
        **{
            story_id: {
                **payload,
                "source_confidence": "transcription",
                "source_type": "WhatsApp audio ASR",
                "source_links": payload["source_links"],
                "unresolved_questions": [payload["unresolved"]],
            }
            for story_id, payload in AUDIO_CARDS.items()
        },
        "US-35": {
            "source_reference": f"{MARIO}; mensajes literales de WhatsApp compartidos en discovery, 12:54–1:01 p.m.",
            "source_attribution": "Mario Groso",
            "source_confidence": "verbatim",
            "source_artifact": {"artifacts": [{
                "artifact_type": "WhatsApp messages as provided by product owner",
                "reference": MARIO,
                "channel": "WhatsApp · copia textual compartida en la conversación de discovery",
                "location": "5/11/2026, 12:54–1:01 p.m.",
                "sha256": None,
            }]},
            "source_links": MARIO_LINKS,
        },
    }

    for story_id, update in updates.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        revised.update({key: value for key, value in update.items() if key != "unresolved"})
        if "unresolved_questions" in update:
            revised["unresolved_questions"] = [*original["unresolved_questions"], *update["unresolved_questions"]]
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
