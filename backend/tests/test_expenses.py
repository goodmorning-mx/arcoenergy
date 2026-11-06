from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation
from app.product_api import ExpenseInput, add_expense, list_expenses
from app.roles import ROLE_PERMISSIONS


def test_accountant_can_record_general_or_project_expenses_with_financial_date() -> None:
    assert "expenses:write" in ROLE_PERMISSIONS["contador"]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        customer = Customer(name="Proyecto solar", city="Tampico")
        db.add(customer)
        db.flush()
        installation = Installation(customer_id=customer.id, lead_installer="campo@example.test")
        db.add(installation)
        db.commit()

        project_expense = add_expense(ExpenseInput(
            installation_id=installation.id,
            category="Combustible",
            description="Gasolina para visita técnica",
            amount=1250,
            occurred_on=date(2026, 11, 5),
        ), identity, db)
        general_expense = add_expense(ExpenseInput(
            category="Servicios",
            description="Internet de oficina",
            amount=850,
            occurred_on=date(2026, 11, 6),
        ), identity, db)
        rows = list_expenses(db)

    assert project_expense["installation_id"] == installation.id
    assert general_expense["installation_id"] is None
    assert [row["project_customer"] for row in rows] == ["Gasto operativo", "Proyecto solar"]
    assert rows[0]["occurred_on"] == date(2026, 11, 6)


def test_installer_must_link_expense_to_own_assigned_installation() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("field-1", "arcoenergy", frozenset({"instalador"}), frozenset({"expenses:write"}), "campo@example.test", "Campo")
    with Session(engine) as db:
        payload = ExpenseInput(category="Viáticos", description="Alimento", amount=150)
        with pytest.raises(HTTPException) as error:
            add_expense(payload, identity, db)

    assert error.value.status_code == 403
