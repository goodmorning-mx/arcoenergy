from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, CashMovement, FinancialAccount
from app.product_api import (
    CashMovementInput,
    CashTransferInput,
    FinancialAccountInput,
    create_cash_movement,
    create_financial_account,
    create_cash_transfer,
    list_financial_accounts,
    reverse_cash_movement,
)
from gm_auth.models import AuthIdentity


def test_cash_movement_and_reversal_keep_auditable_balance() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset(), "admin@example.com", "Admin")
    with Session(engine) as db:
        account = create_financial_account(
            FinancialAccountInput(name="Caja", account_type="cash", opening_balance=Decimal("1000"), opening_balance_date=date.today()),
            identity,
            db,
        )
        movement = create_cash_movement(
            CashMovementInput(account_id=account["id"], direction="out", amount=Decimal("250"), category="Gasto", description="Compra de materiales"),
            identity,
            db,
        )
        reversal = reverse_cash_movement(movement["id"], identity, db)

        rows = list_financial_accounts(db)
        saved = db.get(CashMovement, movement["id"])
        all_movements = db.query(CashMovement).order_by(CashMovement.created_at).all()

    assert rows[0]["current_balance"] == Decimal("1000")
    assert saved is not None and saved.direction == "out"
    assert len(all_movements) == 2
    assert reversal["reversal_of_id"] == movement["id"]


def test_cash_movement_cannot_be_reversed_twice() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset(), "admin@example.com", "Admin")
    with Session(engine) as db:
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=0, opening_balance_date=date.today())
        db.add(account); db.commit(); db.refresh(account)
        movement = CashMovement(account_id=account.id, direction="in", amount=100, category="Cobro", description="Anticipo", source_type="manual", created_by=identity.email)
        db.add(movement); db.commit(); db.refresh(movement)
        reverse_cash_movement(movement.id, identity, db)

        with pytest.raises(HTTPException) as error:
            reverse_cash_movement(movement.id, identity, db)

    assert error.value.status_code == 409


def test_cash_transfer_posts_balanced_pair_and_reversal_corrects_both_accounts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset(), "admin@example.com", "Admin")
    with Session(engine) as db:
        cash = FinancialAccount(name="Caja", account_type="cash", opening_balance=1000, opening_balance_date=date(2026, 1, 1))
        bank = FinancialAccount(name="Banco", account_type="bank", opening_balance=200, opening_balance_date=date(2026, 1, 1))
        db.add_all([cash, bank]); db.commit(); db.refresh(cash); db.refresh(bank)
        transfer = create_cash_transfer(CashTransferInput(
            source_account_id=cash.id, destination_account_id=bank.id,
            amount=Decimal("250.00"), description="Depósito en banco", occurred_on=date(2026, 11, 7),
        ), identity, db)

        assert len(transfer["movements"]) == 2
        assert {row["direction"] for row in transfer["movements"]} == {"in", "out"}
        assert len({row["source_id"] for row in transfer["movements"]}) == 1
        balances = {row["id"]: row["current_balance"] for row in list_financial_accounts(db)}
        assert balances[cash.id] == Decimal("750.00")
        assert balances[bank.id] == Decimal("450.00")
        assert sum(balances.values()) == Decimal("1200.00")

        correction = reverse_cash_movement(transfer["movements"][0]["id"], identity, db)
        assert len(correction["movements"]) == 2
        balances = {row["id"]: row["current_balance"] for row in list_financial_accounts(db)}
        assert balances[cash.id] == Decimal("1000.00")
        assert balances[bank.id] == Decimal("200.00")

        with pytest.raises(HTTPException) as error:
            reverse_cash_movement(transfer["movements"][1]["id"], identity, db)
        assert error.value.status_code == 409


def test_cash_transfer_rejects_same_account_and_pre_opening_date() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), frozenset(), "admin@example.com", "Admin")
    with Session(engine) as db:
        cash = FinancialAccount(name="Caja", account_type="cash", opening_balance=100, opening_balance_date=date(2026, 11, 1))
        bank = FinancialAccount(name="Banco", account_type="bank", opening_balance=200, opening_balance_date=date(2026, 11, 2))
        db.add_all([cash, bank]); db.commit(); db.refresh(cash); db.refresh(bank)
        with pytest.raises(HTTPException) as error:
            create_cash_transfer(CashTransferInput(source_account_id=cash.id, destination_account_id=cash.id, amount=10, description="Mismo origen", occurred_on=date(2026, 11, 7)), identity, db)
        assert error.value.status_code == 422
        with pytest.raises(HTTPException) as error:
            create_cash_transfer(CashTransferInput(source_account_id=cash.id, destination_account_id=bank.id, amount=10, description="Antes del inicio", occurred_on=date(2026, 11, 1)), identity, db)
        assert error.value.status_code == 422
