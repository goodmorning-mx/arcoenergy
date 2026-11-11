"""Append precise source artifact locators to every remaining history card.

Revisions 127–129 added locators for US-33–35 and validation artifacts for US-14/37.
This revision completes exact artifact/paragraph locators for the remaining cards.

Revision ID: 202611110130
Revises: 202611110129
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110130"
down_revision = "202611110129"
branch_labels = None
depends_on = None

ITERATION = "Iteración 118 · ubicaciones fuente para las 42 history cards · 2026-11-11"

ARTIFACTS = {
    "goito": [{
        "artifact_type": "WhatsApp source transcript",
        "reference": "docs/discovery/sources/goito-profugo-whatsapp-2026-10-26.md",
        "channel": "WhatsApp · texto compartido por el dueño del producto",
        "sha256": "d114e973fae8e320dc61692896a918e0309d12f0db2c6ea165aa90863e4a8c90",
    }],
    "contador_word": [
        {
            "artifact_type": "Documento Word original",
            "reference": "docs/discovery/sources/contador-comentarios-mejoras-original.docx",
            "channel": "Word entregado por el contador",
            "sha256": "510e1628af5da03f0091d939de21a0109c806c0f2a9095d0bd1b4ccea06f2205",
        },
        {
            "artifact_type": "Documento PDF original",
            "reference": "docs/discovery/sources/contador-mejoras-original.pdf",
            "channel": "PDF entregado por el contador",
            "sha256": "0c53d6bab43b9cc01a0335925d0093c1b9f9ae3f350d3342b710bef3cad5e60b",
        },
        {
            "artifact_type": "Transcripción textual del Word",
            "reference": "docs/discovery/sources/contador-comentarios-mejoras-transcripcion.md",
            "channel": "Extracción de párrafos del documento Word",
            "sha256": "0e3aefc282a21adc705d383c3923bf544fa79802c10082decfdb5d24c9a0cc9e",
        },
    ],
    "mario": [{
        "artifact_type": "WhatsApp source transcript",
        "reference": "docs/discovery/sources/mario-groso-whatsapp-2026-11-05.md",
        "channel": "WhatsApp · mensajes pegados por el solicitante",
        "sha256": "9843320a1cc669ba116458ce119a0a39b0b6afb2ad7715d0ff11762c024cd5f8",
    }],
    "owner": [{
        "artifact_type": "Conversation source transcript",
        "reference": "docs/discovery/sources/owner-product-brief-2026-11-06.md",
        "channel": "Conversación del proyecto compartida por el dueño del producto",
        "sha256": "88098084577feb24eee03357c1737c1cfaa70e2997db87979f7929c33caba019",
    }],
}

# Exact source locations. Word paragraph/page numbers and transcript line ranges
# were checked against the original DOCX/PDF and its extracted text.
CARD_LOCATORS = {
    "US-1": ("goito", "Mensaje 11:11 p.m., 26/10/2026; fuente espejo línea 10"),
    "US-2": ("goito", "Mensaje 11:12 p.m., 26/10/2026; fuente espejo línea 12"),
    "US-3": ("goito", "Mensaje 11:13 p.m., 26/10/2026; fuente espejo línea 14"),
    "US-4": ("goito", "Mensaje 11:14 p.m., 26/10/2026; fuente espejo línea 16"),
    "US-5": ("goito", "Mensajes duplicados 11:16 p.m., 26/10/2026; fuente espejo líneas 18–20"),
    "US-6": ("goito", "Mensaje 11:16 p.m., 26/10/2026; firma en línea 22"),
    "US-7": ("goito", "Mensaje 11:18 p.m., 26/10/2026; fuente espejo línea 23"),
    "US-8": ("goito", "Mensaje 11:18 p.m., 26/10/2026; fuente espejo línea 24"),
    "US-9": ("goito", "Mensaje 11:19 p.m., 26/10/2026; fuente espejo línea 25"),
    "US-10": ("goito", "Mensaje 11:20 p.m., 26/10/2026; fuente espejo línea 26"),
    "US-11": ("goito", "Mensaje 11:22 p.m., 26/10/2026; fuente espejo línea 27"),
    "US-12": ("goito", "Mensaje 11:22 p.m., 26/10/2026; fuente espejo línea 28"),
    "US-13": ("goito", "Mensajes 11:22–11:23 p.m., 26/10/2026; fuente espejo líneas 29–30"),
    "US-14": ("goito", "Mensaje 11:23 p.m., 26/10/2026; fuente espejo línea 30"),
    "US-15": ("contador_word", "Apartado VENTAS; Word XML párrafos 7–9, PDF pág. 1, transcripción líneas 15–17"),
    "US-16": ("contador_word", "Apartado CLIENTES; Word XML párrafos 9–12, PDF pág. 1, transcripción líneas 19–23"),
    "US-17": ("contador_word", "Apartado GASTOS; Word XML párrafos 12–15, PDF pág. 2, transcripción líneas 25–29"),
    "US-18": ("contador_word", "CUENTAS DE DEBITO Y EFECTIVO; Word XML párrafos 15–17, PDF pág. 2, transcripción líneas 31–33"),
    "US-19": ("contador_word", "DASHBOARD; Word XML párrafos 17–21, PDF pág. 2, transcripción líneas 35–39"),
    "US-20": ("contador_word", "INVENTARIO; Word XML párrafos 21–25, PDF pág. 2, transcripción líneas 41–45"),
    "US-21": ("contador_word", "ENTRADAS (DE INVETARIO); Word XML párrafos 25–32, PDF pág. 2, transcripción líneas 47–57"),
    "US-22": ("contador_word", "Lectura de factura en ENTRADAS; Word XML párrafos 28–29, PDF pág. 2, transcripción línea 51"),
    "US-23": ("contador_word", "Devolución en ENTRADAS; Word XML párrafos 30–31, PDF pág. 2, transcripción línea 55"),
    "US-24": ("contador_word", "SALIDAS (DE INVENTARIO); Word XML párrafos 32–34, PDF pág. 3, transcripción líneas 59–61"),
    "US-25": ("contador_word", "Lectura de orden de servicio; Word XML párrafos 34–35, PDF pág. 3, transcripción línea 63"),
    "US-26": ("contador_word", "Alerta de stock en SALIDAS; Word XML párrafos 35–36, PDF pág. 3, transcripción línea 65"),
    "US-27": ("contador_word", "Apartado KARDEX; Word XML párrafos 36–39, PDF pág. 3, transcripción líneas 67–69"),
    "US-28": ("contador_word", "Apartado ESCANER; Word XML párrafos 39–42, PDF pág. 3, transcripción líneas 71–73"),
    "US-29": ("contador_word", "Apartado REPORTES; Word XML párrafos 42–46, PDF pág. 3, transcripción líneas 75–93"),
    "US-30": ("contador_word", "Apartado PROVEEDORES; Word XML párrafos 52–57, PDF pág. 3, transcripción líneas 95–101"),
    "US-31": ("contador_word", "Pagos a proveedores; Word XML párrafos 57–59, PDF pág. 3, transcripción línea 103"),
    "US-32": ("contador_word", "Apartado PROYECTOS; Word XML párrafos 59–62, PDF pág. 4, transcripción líneas 105–107"),
    "US-36": ("mario", "Mensajes 12:58–1:01 p.m., 5/11/2026; fuente espejo líneas 19–23"),
    "US-37": ("mario", "Mensaje 1:06 p.m., 5/11/2026; fuente espejo línea 30"),
    "US-38": ("mario", "Mensajes 1:16 p.m., 5/11/2026; estado de resultados, fuente espejo líneas 36–49"),
    "US-39": ("owner", "Distribución funcional de portales; fuente espejo línea 10, fragmento CRM"),
    "US-40": ("owner", "Distribución funcional de portales; fuente espejo línea 10, fragmento PWA"),
    "US-41": ("owner", "Distribución funcional de portales; fuente espejo línea 10, fragmento agente/web"),
    "US-42": ("owner", "Diseño e iteración de history cards; mensajes literales, fuente espejo líneas 14–24"),
}


def _artifact_link_indices(source_key: str, first_index: int) -> tuple[list[dict], list[dict]]:
    artifacts = [dict(item, location="") for item in ARTIFACTS[source_key]]
    if source_key == "contador_word":
        relations = ["literal", "literal", "validation"]
    else:
        relations = ["literal"]
    links = [
        {"artifact_index": first_index + offset, "relation": relation}
        for offset, relation in enumerate(relations)
    ]
    return artifacts, links


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)

    for story_id, (source_key, location) in CARD_LOCATORS.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        previous_artifacts = list((original["source_artifact"] or {}).get("artifacts", []))
        new_artifacts, new_links = _artifact_link_indices(source_key, len(previous_artifacts))
        for link in new_links:
            link["location"] = location

        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "source_reference": f"{original['source_reference']}; localizador de fuente: {location}",
            "source_artifact": {"artifacts": [*previous_artifacts, *new_artifacts]},
            "source_links": [*(original["source_links"] or []), *new_links],
            "source_confidence": "verbatim",
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        if story_id == "US-42":
            revised["acceptance_criteria"] = [
                *original["acceptance_criteria"],
                "Las 42 story cards conservan su source_literal y cuentan con artefactos hasheados y ubicaciones de origen: mensajes, párrafos/páginas de Word/PDF, transcripción ASR o bundle validado.",
                "La procedencia precisa diferencia texto literal, transcripción ASR y artefactos de validación; nunca convierte ASR o reconstrucción en cita humana confirmada.",
            ]
            revised["unresolved_questions"] = [
                *original["unresolved_questions"],
                "La ubicación del texto y el hash del artefacto prueban trazabilidad, no aprobación de la interpretación por cada stakeholder; faltan validación humana de ASR y cotejo de las tarjetas reconstruidas.",
            ]
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
