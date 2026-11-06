from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, CashMovement, FinancialAccount
from app.product_api import (
    CashMovementInput,
    FinancialAccountInput,
    create_cash_movement,
    create_financial_account,
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
