from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, CashMovement, Customer, FinancialAccount, Installation
from app.product_api import ExpenseInput, PaymentCorrectionInput, add_expense, list_expenses, list_financial_accounts, reverse_expense
from app.roles import ROLE_PERMISSIONS


def test_accountant_can_record_general_or_project_expenses_with_financial_date() -> None:
    assert "expenses:write" in ROLE_PERMISSIONS["contador"]
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        customer = Customer(name="Proyecto solar", city="Tampico")
        account = FinancialAccount(name="Caja chica", account_type="cash", opening_balance=5000, opening_balance_date=date(2026, 11, 1))
        db.add(customer)
        db.add(account)
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
            account_id=account.id,
        ), identity, db)
        general_expense = add_expense(ExpenseInput(
            category="Servicios",
            description="Internet de oficina",
            amount=850,
            occurred_on=date(2026, 11, 6),
            account_id=account.id,
        ), identity, db)
        rows = list_expenses(db)
        linked_movements = db.query(CashMovement).filter(CashMovement.source_type == "expense").all()
        current_balance = list_financial_accounts(db)[0]["current_balance"]
        linked_amount = sum(row.amount for row in linked_movements)

    assert project_expense["installation_id"] == installation.id
    assert general_expense["installation_id"] is None
    assert [row["project_customer"] for row in rows] == ["Gasto operativo", "Proyecto solar"]
    assert rows[0]["occurred_on"] == date(2026, 11, 6)
    assert rows[0]["account_name"] == "Caja chica"
    assert len(linked_movements) == 2
    assert linked_amount == 2100
    assert current_balance == 2900


def test_accountant_must_select_an_active_account_for_expense() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        with pytest.raises(HTTPException) as error:
            add_expense(ExpenseInput(category="Servicios", description="Internet de oficina", amount=850), identity, db)
    assert error.value.status_code == 422


def test_installer_must_link_expense_to_own_assigned_installation() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("field-1", "arcoenergy", frozenset({"instalador"}), frozenset({"expenses:write"}), "campo@example.test", "Campo")
    with Session(engine) as db:
        payload = ExpenseInput(category="Viáticos", description="Alimento", amount=150)
        with pytest.raises(HTTPException) as error:
            add_expense(payload, identity, db)

    assert error.value.status_code == 403


def test_expense_correction_appends_offset_and_restores_linked_account() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        account = FinancialAccount(name="Banco operativo", account_type="bank", opening_balance=10000, opening_balance_date=date(2026, 11, 1))
        db.add(account)
        db.commit()
        expense = add_expense(ExpenseInput(category="Servicios", expense_type="fixed", description="Pago duplicado", amount=750, account_id=account.id), identity, db)
        correction = reverse_expense(expense["id"], PaymentCorrectionInput(reason="Captura duplicada"), identity, db)
        rows = list_expenses(db)
        movements = db.query(CashMovement).order_by(CashMovement.created_at).all()
        balance = list_financial_accounts(db)[0]["current_balance"]
        with pytest.raises(HTTPException) as error:
            reverse_expense(expense["id"], PaymentCorrectionInput(reason="Segundo intento"), identity, db)

    assert correction["reversal_of_id"] == expense["id"]
    assert correction["amount"] == -750
    assert correction["expense_type"] == expense["expense_type"] == "fixed"
    assert sum(row["amount"] for row in rows) == 0
    assert len(movements) == 2
    assert movements[1].direction == "in"
    assert movements[1].reversal_of_id == movements[0].id
    assert balance == 10000
    assert error.value.status_code == 409


def test_installer_cannot_correct_expenses() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("field-1", "arcoenergy", frozenset({"instalador"}), frozenset({"expenses:write"}), "campo@example.test", "Campo")
    with Session(engine) as db:
        with pytest.raises(HTTPException) as error:
            reverse_expense("missing", PaymentCorrectionInput(reason="Error de captura"), identity, db)
    assert error.value.status_code == 403
