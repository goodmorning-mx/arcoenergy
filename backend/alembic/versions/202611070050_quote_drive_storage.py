"""Store generated quote PDFs in private Google Drive when authorized.

Revision ID: 202611070050
Revises: 202611070049
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070050"
down_revision = "202611070049"
branch_labels = None
depends_on = None


def _append_revision(bind, history, story_id, iteration, criteria, questions):
    original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": iteration,
        "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
        "unresolved_questions": [*original["unresolved_questions"], *questions],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    op.bulk_insert(history, [revised])


def upgrade() -> None:
    op.add_column("ae_quotes", sa.Column("drive_file_id", sa.String(length=200), nullable=False, server_default=""))
    bind = op.get_bind()
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    iteration = "Iteración 39 · archivo privado de cotizaciones en Drive · 2026-11-07"
    _append_revision(
        bind, history, "US-3", iteration,
        ["Al generar el PDF de una cotización, la API lo guarda o reemplaza en la carpeta privada de Drive configurada y conserva el ID del archivo.",
         "La interfaz distingue el archivo guardado en Drive de los casos donde faltan credenciales o falla la carga; descargar el PDF no se presenta como respaldo en Drive."],
        ["La integración cubre PDFs de cotización; contratos, identificaciones, recibos y otros datos aún no se almacenan ni sincronizan en Drive.",
         "La instancia debe configurar una cuenta de servicio autorizada y compartir con ella la carpeta privada destino."],
    )
    _append_revision(
        bind, history, "US-13", iteration,
        ["El estado de Drive solo indica conexión cuando la API valida con credenciales una carpeta de Drive accesible.",
         "Los PDFs de cotización aprobados se cargan a dicha carpeta y sus metadatos quedan relacionados con el folio."],
        ["No se cargan automáticamente contratos, identificaciones, CFDI, gastos ni datos operativos generales.",
         "Falta acordar retención, restauración, borrado, auditoría de acceso y respaldo para todos los tipos de archivo."],
    )


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(
        history.c.iteration == "Iteración 39 · archivo privado de cotizaciones en Drive · 2026-11-07",
        history.c.recorded_by == "system:implementation-iteration",
    ))
    op.drop_column("ae_quotes", "drive_file_id")
