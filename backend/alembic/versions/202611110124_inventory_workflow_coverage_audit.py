"""Record verified inventory workflow coverage across four source cards.

Revision ID: 202611110124
Revises: 202611110123
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611110124"
down_revision = "202611110123"
branch_labels = None
depends_on = None

ITERATION = "Iteración 112 · auditoría funcional de inventario · 2026-11-11"
CRITERIA = {
    "US-20": (
        "El catálogo captura y conserva nombre, descripción, categoría/subcategoría, marca, modelo, proveedor, unidad y código QR/barras; CRM imprime la etiqueta e interfaces móviles ofrecen lectura asistida.",
        "Validar unidades de medida, impresión y lectura con el equipo y el material real de almacén.",
    ),
    "US-24": (
        "Las cantidades solicitadas, reservadas/entregadas, consumidas y devueltas se distinguen por orden; salidas y consumo están enlazados al artículo, costo y proyecto sin descontar dos veces.",
        "Acordar autorización formal de variaciones y observar la rutina de entrega/devolución en una instalación real.",
    ),
    "US-26": (
        "Administración configura mínimo y responsable de reabasto por artículo; Web Push se programa al cruzar el umbral, se deduplica y se rearma al recuperar existencias.",
        "Confirmar recepción de Web Push en los modelos de teléfono y cuentas de instalador usados por el equipo.",
    ),
    "US-27": (
        "CRM filtra movimientos por artículo y fechas, pagina el intervalo y permite exportación CSV completa; costos históricos se muestran solo a identidades autorizadas.",
        "Medir rendimiento y validar cobertura de costos históricos con el kardex real del almacén.",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criterion, unresolved) in CRITERIA.items():
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
            "acceptance_criteria": [*original["acceptance_criteria"], criterion],
            "unresolved_questions": [*original["unresolved_questions"], unresolved],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        op.bulk_insert(history, [revised])


def downgrade() -> None:
    history = sa.table("ae_history_cards", sa.column("iteration", sa.String()), sa.column("recorded_by", sa.String()))
    op.execute(sa.delete(history).where(history.c.iteration == ITERATION, history.c.recorded_by == "system:implementation-iteration"))
