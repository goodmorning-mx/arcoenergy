"""Introduce project records and link work orders and expenses.

Revision ID: 202611100080
Revises: 202611100079
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611100080"
down_revision = "202611100079"
branch_labels = None
depends_on = None

ITERATION = "Iteración 68 · proyectos y códigos únicos · 2026-11-10"
CRITERIA = [
    "Un proyecto conserva un código único, nombre, cliente y notas, y aparece en un apartado CRM propio.",
    "Las órdenes de trabajo y los gastos pueden vincularse con el proyecto; al crear una orden sin proyecto, el sistema crea uno automáticamente.",
    "La migración conserva las órdenes y gastos anteriores y les agrega un proyecto sin alterar sus movimientos ni importes.",
]
QUESTIONS = [
    "Validar con administración el formato comercial del código de proyecto y si un proyecto puede tener varias órdenes de instalación.",
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_projects"):
        op.create_table(
            "ae_projects",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("code", sa.String(length=40), nullable=False, unique=True),
            sa.Column("customer_id", sa.String(length=36), sa.ForeignKey("ae_customers.id"), nullable=False),
            sa.Column("name", sa.String(length=180), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_by", sa.String(length=180), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    for table_name in ("ae_installations", "ae_expenses"):
        if not sa.inspect(bind).has_table(table_name):
            continue
        columns = {column["name"] for column in sa.inspect(bind).get_columns(table_name)}
        if "project_id" not in columns:
            op.add_column(table_name, sa.Column(
                "project_id", sa.String(length=36), sa.ForeignKey("ae_projects.id"), nullable=True,
            ))
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("ae_projects")}
    if "ix_ae_projects_code" not in indexes:
        op.create_index("ix_ae_projects_code", "ae_projects", ["code"], unique=False)
    for table_name in ("ae_installations", "ae_expenses"):
        if sa.inspect(bind).has_table(table_name):
            indexes = {index["name"] for index in sa.inspect(bind).get_indexes(table_name)}
            name = f"ix_{table_name}_project_id"
            if name not in indexes:
                op.create_index(name, table_name, ["project_id"])

    if sa.inspect(bind).has_table("ae_installations"):
        installations = sa.Table("ae_installations", sa.MetaData(), autoload_with=bind)
        customers = sa.Table("ae_customers", sa.MetaData(), autoload_with=bind)
        projects = sa.Table("ae_projects", sa.MetaData(), autoload_with=bind)
        created_at = datetime.now(timezone.utc)
        for installation in bind.execute(sa.select(installations).where(installations.c.project_id.is_(None))).mappings():
            customer = bind.execute(sa.select(customers.c.id, customers.c.name).where(customers.c.id == installation["customer_id"])).mappings().first()
            if customer is None:
                continue
            project_id = str(uuid4())
            project_code = f"AE-P-LEG-{uuid4().hex[:8].upper()}"
            bind.execute(projects.insert().values(
                id=project_id, code=project_code, customer_id=customer["id"],
                name=customer["name"], notes=f"Proyecto migrado de la orden {installation['folio'] or installation['id']}.",
                created_by="system:project-migration", created_at=created_at,
            ))
            bind.execute(installations.update().where(installations.c.id == installation["id"]).values(project_id=project_id))

    if sa.inspect(bind).has_table("ae_expenses") and sa.inspect(bind).has_table("ae_installations"):
        expenses = sa.Table("ae_expenses", sa.MetaData(), autoload_with=bind)
        installations = sa.Table("ae_installations", sa.MetaData(), autoload_with=bind)
        for expense, project_id in bind.execute(sa.select(expenses.c.id, installations.c.project_id)
                .join(installations, installations.c.id == expenses.c.installation_id)
                .where(expenses.c.project_id.is_(None), expenses.c.installation_id.is_not(None))).all():
            bind.execute(expenses.update().where(expenses.c.id == expense).values(project_id=project_id))

    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    original = bind.execute(sa.select(history).where(history.c.story_id == "US-32").order_by(history.c.version.desc())).mappings().first()
    if original is not None:
        revised = dict(original)
        revised.update({
            "id": str(uuid4()), "version": original["version"] + 1, "iteration": ITERATION,
            "acceptance_criteria": [*original["acceptance_criteria"], *CRITERIA],
            "unresolved_questions": [*original["unresolved_questions"], *QUESTIONS],
            "recorded_by": "system:implementation-iteration", "created_at": datetime.now(timezone.utc),
        })
        bind.execute(history.insert().values(**revised))


def downgrade() -> None:
    pass
