"""Archive work-order requests privately and record access audit iteration.

Revision ID: 202611070052
Revises: 202611070051
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611070052"
down_revision = "202611070051"
branch_labels = None
depends_on = None

ITERATION = "Iteración 41 · archivo de solicitudes y auditoría de acceso real · 2026-11-07"


def _append_revision(bind, history, story_id, criteria, questions):
    original = bind.execute(sa.select(history).where(history.c.story_id == story_id)
                            .order_by(history.c.version.desc())).mappings().first()
    if original is None:
        return
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


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_installations")}
    additions = (
        ("material_request_drive_file_id", sa.String(200), False, ""),
        ("material_request_filename", sa.String(255), False, ""),
        ("material_request_content_type", sa.String(100), False, ""),
        ("material_request_updated_at", sa.DateTime(timezone=True), True, None),
    )
    for name, type_, nullable, default in additions:
        if name not in columns:
            options = {"nullable": nullable}
            if default is not None:
                options["server_default"] = default
            op.add_column("ae_installations", sa.Column(name, type_, **options))

    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    _append_revision(
        bind, history, "US-25",
        ["Almacén puede adjuntar PDF, JPG, PNG o WebP de hasta 12 MB a una orden; la API valida tipo/contenido y lo guarda en Drive privado si la conexión está autorizada.",
         "Personal con permiso de salida puede recuperar el archivo mediante un endpoint autenticado; los metadatos quedan ligados a la orden.",
         "La interfaz informa expresamente si Drive no está configurado o falla, y no afirma que el archivo quedó archivado."],
        ["La instancia DEV aún requiere credenciales y carpeta privada de Drive autorizadas para que la carga se complete.",
         "El reconocimiento OCR de solicitudes manuscritas continúa fuera de alcance; las cantidades se transcriben y revisan manualmente."],
    )
    _append_revision(
        bind, history, "US-13",
        ["El cliente privado de Drive también permite conservar y recuperar la solicitud de materiales vinculada a una orden de trabajo."],
        ["Esta extensión cubre únicamente PDFs de cotización y solicitudes de materiales cuando Drive está conectado; contratos, INE, recibos y sincronización general siguen pendientes."],
    )
    _append_revision(
        bind, history, "US-14",
        ["DEV sirve la entrada de escritorio en /login y /crm/login, y la de PWA en /app/login; CRM/PWA redirigen sesiones no autenticadas a su acceso correspondiente."],
        ["El inventario DEV revisado contiene una sola cuenta administradora; falta cargar y validar cuentas reales de contador, marketing, instalador y cliente con sus responsables."],
    )
    _append_revision(
        bind, history, "US-39",
        ["La compilación activa revisada no presenta sello, contador ni acceso de prueba/demo; el acceso requiere una cuenta autenticada."],
        ["Falta confirmar las cuentas y datos reales del equipo para completar la puesta en marcha comercial."],
    )
    _append_revision(
        bind, history, "US-40",
        ["La entrada protegida de PWA dirige a /app/login y comparte el acceso de la cuenta autorizada de campo/cliente."],
        ["Aún no existen cuentas reales de instalador o cliente en la organización DEV revisada."],
    )


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("ae_installations")}
    for name in ("material_request_updated_at", "material_request_content_type", "material_request_filename", "material_request_drive_file_id"):
        if name in columns:
            op.drop_column("ae_installations", name)
