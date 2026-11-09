"""Classify operating expenses as fixed, variable or legacy unclassified.

Revision ID: 202611090078
Revises: 202611090077
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611090078"
down_revision = "202611090077"
branch_labels = None
depends_on = None

ITERATION = "Iteración 66 · gastos fijos y variables · 2026-11-09"
REVISIONS = {
    "US-17": (
        [
            "Los nuevos gastos operativos se clasifican explícitamente como fijos o variables y conservan la clasificación al corregirse.",
            "Los registros heredados sin clasificación permanecen como no clasificados; no se infiere su naturaleza.",
        ],
        ["El contador debe validar cómo clasificar gastos mixtos y qué conceptos recurrentes representan cada categoría."],
    ),
    "US-38": (
        [
            "Los reportes por proyecto y periodo separan los gastos fijos, variables y no clasificados, además de conservar el total operativo.",
        ],
        ["Los estados financieros formales, devoluciones/bonificaciones y la validación de fórmulas por contabilidad continúan pendientes."],
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("ae_expenses"):
        columns = {column["name"] for column in inspector.get_columns("ae_expenses")}
        if "expense_type" not in columns:
            op.add_column("ae_expenses", sa.Column(
                "expense_type", sa.String(length=20), nullable=False, server_default="unclassified",
            ))
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    for story_id, (criteria, questions) in REVISIONS.items():
        original = bind.execute(
            sa.select(history).where(history.c.story_id == story_id).order_by(history.c.version.desc())
        ).mappings().first()
        if original is None:
            continue
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1,
            "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *criteria],
            "unresolved_questions": [*original["unresolved_questions"], *questions],
            "recorded_by": "system:implementation-iteration",
            "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
