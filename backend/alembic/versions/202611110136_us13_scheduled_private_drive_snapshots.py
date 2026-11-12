"""Track scheduled private business snapshots uploaded to Drive.

Revision ID: 202611110136
Revises: 202611110135
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110136"
down_revision = "202611110135"
branch_labels = None
depends_on = None

ITERATION = "Iteración 124 · respaldo periódico privado en Drive · 2026-11-11"


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_business_snapshot_runs"):
        op.create_table(
            "ae_business_snapshot_runs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("filename", sa.String(length=255), nullable=False),
            sa.Column("file_bytes", sa.Integer(), nullable=False),
            sa.Column("record_count", sa.Integer(), nullable=False),
            sa.Column("error_code", sa.String(length=80), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("ae_business_snapshot_runs")}
    if "ix_ae_business_snapshot_runs_status_started" not in indexes:
        op.create_index(
            "ix_ae_business_snapshot_runs_status_started",
            "ae_business_snapshot_runs", ["status", "started_at"],
        )

    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(
        sa.select(history).where(history.c.story_id == "US-13").order_by(history.c.version.desc())
    ).mappings().first()
    if original is None:
        return

    revised = dict(original)
    revised.update({
        "id": str(uuid4()),
        "version": original["version"] + 1,
        "iteration": ITERATION,
        "acceptance_criteria": [
            *original["acceptance_criteria"],
            "Cuando carpeta y credenciales privadas de Drive están configuradas, el servicio genera y archiva una copia JSON automática cada intervalo configurado (24 horas por defecto).",
            "La API persiste estado, hora, nombre de archivo y conteo del respaldo; errores se reintentan sin informar éxito falso.",
            "La ejecución periódica no duplica respaldos entre réplicas PostgreSQL y no depende de que un administrador mantenga abierta la aplicación.",
        ],
        "unresolved_questions": [
            *original["unresolved_questions"],
            "La programación queda inactiva hasta configurar y verificar la carpeta y cuenta de servicio privadas en DEV.",
            "Retención, restauración y validación de permisos/recuperación requieren política administrativa y ejercicio de restauración separado.",
        ],
        "recorded_by": "system:implementation-iteration",
        "created_at": datetime.now(timezone.utc),
    })
    bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
