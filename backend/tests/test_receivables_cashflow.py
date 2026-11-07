from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, CashMovement, Customer, CustomerPayment, FinancialAccount, Receivable
from app.product_api import PaymentCorrectionInput, PaymentInput, list_financial_accounts, list_receivables, record_payment, reverse_customer_payment
from app.roles import ROLE_PERMISSIONS


def test_customer_payments_update_receivable_and_cash_account() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        customer = Customer(name="Cliente solar", phone="8331234567", city="Tampico")
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=1000, opening_balance_date=date.today())
        db.add_all([customer, account]); db.flush()
        receivable = Receivable(customer_id=customer.id, amount=900, paid_amount=0, due_date=date.today() + timedelta(days=3), payment_method="Transferencia")
        db.add(receivable); db.commit(); db.refresh(receivable)

        first = record_payment(receivable.id, PaymentInput(amount=300, account_id=account.id, paid_on=date.today(), reference="TRX-1"), identity, db)
        after_first = list_receivables(db)[0]
        second = record_payment(receivable.id, PaymentInput(amount=600, account_id=account.id, paid_on=date.today(), reference="TRX-2"), identity, db)
        cash_balance = list_financial_accounts(db)[0]["current_balance"]
        payments = db.scalars(select(CustomerPayment).where(CustomerPayment.receivable_id == receivable.id)).all()
        movements = db.scalars(select(CashMovement).where(CashMovement.source_type == "customer_payment")).all()

        with pytest.raises(HTTPException) as error:
            record_payment(receivable.id, PaymentInput(amount=1, account_id=account.id), identity, db)

    assert after_first["balance"] == Decimal("600.00")
    assert after_first["status"] == "partial"
    assert len(after_first["payments"]) == 1
    assert after_first["payments"][0]["account_name"] == "Banco"
    assert second["balance"] == Decimal("0.00")
    assert second["status"] == "paid"
    assert cash_balance == Decimal("1900.00")
    assert len(payments) == len(movements) == 2
    assert sum((Decimal(row.amount) for row in payments), Decimal("0")) == Decimal("900.00")
    assert error.value.status_code == 409


def test_reversing_customer_payment_restores_receivable_and_cash_with_append_only_history() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
    with Session(engine) as db:
        customer = Customer(name="Cliente solar")
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=0, opening_balance_date=date.today())
        db.add_all([customer, account]); db.flush()
        receivable = Receivable(customer_id=customer.id, amount=700, paid_amount=0, due_date=date.today() + timedelta(days=10), payment_method="Transferencia")
        db.add(receivable); db.commit(); db.refresh(receivable); db.refresh(account)
        record_payment(receivable.id, PaymentInput(amount=250, account_id=account.id, paid_on=date.today(), reference="TRX-250"), identity, db)
        original_payment = db.scalars(select(CustomerPayment).where(CustomerPayment.receivable_id == receivable.id)).one()

        corrected = reverse_customer_payment(
            receivable.id, original_payment.id,
            PaymentCorrectionInput(reason="El banco rechazó la transferencia"), identity, db,
        )
        payments = db.scalars(select(CustomerPayment).where(CustomerPayment.receivable_id == receivable.id)).all()
        movements = db.scalars(select(CashMovement).where(CashMovement.account_id == account.id).order_by(CashMovement.created_at)).all()
        bank_balance = list_financial_accounts(db)[0]["current_balance"]

    assert corrected["paid_amount"] == Decimal("0.00")
    assert corrected["balance"] == Decimal("700.00")
    assert corrected["status"] == "pending"
    assert len(payments) == len(movements) == 2
    assert payments[1].reversal_of_id == original_payment.id
    assert movements[1].reversal_of_id == movements[0].id
    assert bank_balance == Decimal("0.00")
