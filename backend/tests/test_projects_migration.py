import importlib.util
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, Customer, HistoryCard, Installation, InventoryMovement, Project, ProjectExpense
from app.product_api import profitability_report


def test_project_migration_backfills_work_orders_and_expenses_and_appends_story_version() -> None:
    path = Path(__file__).parents[1] / "alembic" / "versions" / "202611100080_projects.py"
    spec = importlib.util.spec_from_file_location(path.name, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    customer = Customer(name="Cliente migrado")
    with engine.begin() as connection:
        connection.execute(Customer.__table__.insert(), {"id": "customer", "name": customer.name, "phone": "", "email": "", "city": "Tampico", "address": "", "status": "lead", "source": "crm"})
        connection.execute(Installation.__table__.insert(), {"id": "order", "customer_id": "customer", "project_id": None, "folio": "AE-OT-1", "lead_installer": "", "status": "assigned", "checklist": [], "notes": ""})
        connection.execute(ProjectExpense.__table__.insert(), {"id": "expense", "installation_id": "order", "project_id": None, "category": "Viáticos", "expense_type": "variable", "description": "Gasolina", "amount": 100, "occurred_on": date(2026, 11, 10), "receipt_url": "", "receipt_drive_file_id": "", "receipt_filename": "", "receipt_content_type": "", "account_id": None, "reversal_of_id": None, "created_by": "test"})
        connection.execute(HistoryCard.__table__.insert(), {"id": str(uuid4()), "story_id": "US-32", "version": 1, "iteration": "initial", "stakeholder": "Contador", "source_type": "document", "source_reference": "word", "source_literal": "Crear proyectos con folio.", "normalized_story": "Proyectos", "acceptance_criteria": [], "unresolved_questions": [], "linked_cards": [], "recorded_by": "source-import", "created_at": datetime.now(timezone.utc)})
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        order = connection.execute(select(Installation.__table__.c.project_id).where(Installation.__table__.c.id == "order")).scalar_one()
        expense = connection.execute(select(ProjectExpense.__table__.c.project_id).where(ProjectExpense.__table__.c.id == "expense")).scalar_one()
        project = connection.execute(select(Project.__table__.c.code).where(Project.__table__.c.id == order)).scalar_one()
        cards = connection.execute(select(HistoryCard.__table__.c.version).where(HistoryCard.__table__.c.story_id == "US-32")).scalars().all()
    assert order == expense
    assert project.startswith("AE-P-LEG-")
    assert sorted(cards) == [1, 2]


def test_profitability_groups_multiple_orders_and_direct_expenses_under_project() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        customer = Customer(name="Cliente solar", city="Tampico")
        db.add(customer); db.flush()
        project = Project(code="AE-P-2026-ABC12345", customer_id=customer.id, name="Sistema Tampico")
        db.add(project); db.flush()
        orders = [Installation(customer_id=customer.id, project_id=project.id, folio=f"AE-OT-{index}") for index in (1, 2)]
        db.add_all(orders); db.flush()
        db.add_all([
            ProjectExpense(project_id=project.id, category="Viáticos", expense_type="variable", description="Traslado", amount=250, occurred_on=date(2026, 11, 9)),
            ProjectExpense(project_id=project.id, installation_id=orders[0].id, category="Mano de obra", expense_type="variable", description="Apoyo", amount=750, occurred_on=date(2026, 11, 9)),
            InventoryMovement(item_id="panel", installation_id=orders[1].id, quantity=2, movement_type="consumption", unit_cost=1000, reason="Instalación", created_at=datetime(2026, 11, 9, tzinfo=timezone.utc)),
        ])
        db.commit()
        report = profitability_report(month="2026-11", project_id=project.id, db=db)
    assert len(report["rows"]) == 1
    assert report["rows"][0]["project_code"] == "AE-P-2026-ABC12345"
    assert report["rows"][0]["expenses"] == 1000
    assert report["rows"][0]["materials_cost"] == 2000
