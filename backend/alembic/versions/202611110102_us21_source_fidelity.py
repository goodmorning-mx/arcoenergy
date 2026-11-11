"""Append the complete original contador source text for US-21.

Revision ID: 202611110102
Revises: 202611110101
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611110102"
down_revision = "202611110101"
branch_labels = None
depends_on = None

ITERATION = "Iteración 90 · fidelidad de fuente US-21 · 2026-11-11"
SOURCE_LITERAL = 'ENTRADAS (DE INVETARIO)\n\nEn entradas es para poder dar de alta los artículos que entran a almacén y que compramos con los proveedores, para ello se debe registrar en el botón de “nueva entrada” con los datos de proveedor, nombre y código del artículo, factura relacionada (en caso de tener), costo unitario del producto, con qué tarjeta fue pagada o si fue pagada en efectivo o a crédito y por último la cantidad que entra al almacén y que permita añadir mas productos por orden de entrada.\n\nUna buena idea es que en el botón de “Nueva entrada” nos permita leer directamente subiendo una factura, el XML, por fotografía de la factura.\n\nTambién requerimos un botón de “añadir articulo” en la “Nueva entrada” que nos permita capturar dos o más artículos en una sola orden de entrada.\n\nAñadir un botón de devolución de artículos para cuando sobre de una instalación poder regresar los sobrantes y que estos no afecten al coste del proyecto.\n\nTambién estaría bien una opción para saber si la entrada fue a crédito o de contado, y con qué medio fue pagada.'


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-21").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "source_literal": SOURCE_LITERAL,
        "source_reference": "docs/discovery/sources/contador-comentarios-mejoras-original.docx; docs/discovery/sources/contador-mejoras-original.pdf; apartado ENTRADAS (DE INVETARIO)",
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "La fuente original incluye lectura/carga desde factura, XML o fotografía para revisión.",
            "Registrar devolución de sobrantes de instalación para regresarlos al almacén sin afectar el costo del proyecto.",
            "Registrar si la entrada es a crédito o de contado y el medio de pago.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "Definir cómo el reconocimiento de factura/XML/fotografía propone datos y quién confirma la entrada.",
            "Definir el enlace entre devolución de sobrantes, movimiento original y costo del proyecto.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
