"""Store reviewed purchase invoice sources in private Drive when configured.

Revision ID: 202611070054
Revises: 202611070053
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070054"
down_revision = "202611070053"
branch_labels = None
depends_on = None

ITERATION = "Iteración 43 · archivo de facturas de compra revisadas · 2026-11-07"


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_purchases")}
    additions = (
        ("invoice_drive_file_id", sa.String(200), False, ""),
        ("invoice_filename", sa.String(255), False, ""),
        ("invoice_content_type", sa.String(100), False, ""),
        ("invoice_updated_at", sa.DateTime(timezone=True), True, None),
    )
    for name, type_, nullable, default in additions:
        if name not in columns:
            options = {"nullable": nullable}
            if default is not None:
                options["server_default"] = default
            op.add_column("ae_purchases", sa.Column(name, type_, **options))

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    revisions = {
        "US-13": (
            ["Los archivos fuente de una compra (CFDI XML validado, PDF o fotografía) pueden quedar archivados en Drive privado y enlazados con el folio de compra."],
            ["Esta extensión archiva la fuente de facturas solo si Drive tiene credenciales y carpeta autorizadas; no sincroniza datos contables completos."],
        ),
        "US-21": (
            ["La compra registrada expone metadatos y descarga autenticada de la factura fuente cuando esta quedó archivada."],
            ["Impuestos, fletes y descuentos globales conservan el tratamiento manual pendiente de acuerdo con el contador."],
        ),
        "US-22": (
            ["El XML CFDI válido propone proveedor, fecha, referencia, conceptos y costos para revisión humana; el archivo puede archivarse ligado a la compra confirmada.",
             "PDF o fotografía de factura pueden adjuntarse a la compra revisada; los campos se capturan manualmente y el sistema no afirma que hizo OCR."],
            ["No hay OCR para fotografías/PDF ni conciliación automática de artículos, impuestos, fletes y descuentos globales.",
             "Drive debe conectarse y tener política de conservación autorizada para que los archivos queden realmente guardados."],
        ),
    }
    for story_id, (criteria, questions) in revisions.items():
        original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                                .order_by(history.c.version.desc())).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()),
            "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_purchases")}
    for name in ("invoice_updated_at", "invoice_content_type", "invoice_filename", "invoice_drive_file_id"):
        if name in columns:
            op.drop_column("ae_purchases", name)

