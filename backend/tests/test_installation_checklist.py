import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Activity, Base, Customer, Installation
from app.product_api import InstallationChecklistInput, InstallationChecklistItemInput, update_installation_checklist
from app.roles import ROLE_PERMISSIONS


def test_assigned_installer_updates_existing_checklist_and_creates_activity() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Campo")
    with Session(engine) as db:
        customer = Customer(name="Cliente solar")
        db.add(customer); db.flush()
        order = Installation(customer_id=customer.id, folio="AE-OT-CHECK", lead_installer="field@example.test",
            checklist=[{"task": "Confirmar materiales", "done": False}, {"task": "Visita de instalación", "done": False}])
        db.add(order); db.commit()
        result = update_installation_checklist(order.id, InstallationChecklistInput(checklist=[
            InstallationChecklistItemInput(task="Confirmar materiales", done=True),
            InstallationChecklistItemInput(task="Visita de instalación", done=False),
        ]), installer, db)
        activities = db.scalars(select(Activity).where(Activity.customer_id == customer.id)).all()

    assert result["checklist"][0]["done"] is True
    assert len(activities) == 1
    assert activities[0].note == "AE-OT-CHECK · Confirmar materiales: completada"


def test_installer_cannot_edit_another_installers_order_or_add_tasks() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Campo")
    with Session(engine) as db:
        customer = Customer(name="Cliente solar")
        db.add(customer); db.flush()
        order = Installation(customer_id=customer.id, lead_installer="other@example.test", checklist=[{"task": "Visita", "done": False}])
        db.add(order); db.commit()
        with pytest.raises(HTTPException) as unauthorized:
            update_installation_checklist(order.id, InstallationChecklistInput(checklist=[InstallationChecklistItemInput(task="Visita", done=True)]), installer, db)
        assert unauthorized.value.status_code == 403
        manager = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
        with pytest.raises(HTTPException) as invalid_task:
            update_installation_checklist(order.id, InstallationChecklistInput(checklist=[InstallationChecklistItemInput(task="Tarea inventada", done=True)]), manager, db)
        assert invalid_task.value.status_code == 422
