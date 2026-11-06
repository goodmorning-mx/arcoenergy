from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity, memberships, users

from app.models import Base, CashMovement, Customer, FinancialAccount, Installation, InventoryItem, InventoryMovement, Quote, Receivable, Sale
from app.product_api import SaleInput, SaleMaterialInput, create_sale, list_financial_accounts
from app.roles import ROLE_PERMISSIONS
from app import product_api


def installer_directory():
    engine = create_engine("sqlite://")
    users.metadata.create_all(engine)
    with engine.begin() as connection:
        now = datetime.now(timezone.utc)
        connection.execute(users.insert().values(id="installer-1", email="field@example.test", name="Instalador", password_hash="unused", is_active=True, created_at=now))
        connection.execute(memberships.insert().values(user_id="installer-1", organization_id=product_api.settings.organization_id, roles=["instalador"], permissions=[], created_at=now))
    return engine


def test_cash_sale_creates_folio_work_order_stock_output_and_cash_inflow(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente Solar", city="Tampico")
        quote = Quote(folio="AE-Q-1", customer_id="", panel_count=8, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 5 kW", payment_method="Contado", panel_subtotal=80000,
            structure_cost=10000, inverter_cost=15000, total=105000, status="accepted", pricing_approved=True)
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=200000, opening_balance_date=date.today())
        item = InventoryItem(name="Panel 600 W", unit="pza", quantity=12, minimum_quantity=2, unit_cost=900)
        db.add_all([customer, account, item]); db.flush(); quote.customer_id = customer.id
        db.add(quote); db.commit(); db.refresh(quote); db.refresh(item); db.refresh(account)

        created = create_sale(SaleInput(quote_id=quote.id, sale_type="cash", account_id=account.id,
            lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=8)]), identity, db)
        current_stock = db.get(InventoryItem, item.id).quantity
        order = db.get(Installation, created["installation_id"])
        movements = db.scalars(select(InventoryMovement).where(InventoryMovement.installation_id == order.id)).all()
        sale = db.get(Sale, created["id"])
        cash_movements = db.scalars(select(CashMovement).where(CashMovement.source_type == "sale")).all()
        current_cash = list_financial_accounts(db)[0]["current_balance"]
        with pytest.raises(HTTPException) as error:
            create_sale(SaleInput(quote_id=quote.id, sale_type="cash", account_id=account.id,
                lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=1)]), identity, db)

    assert sale.folio.startswith("AE-V-")
    assert order.folio and order.folio.startswith("AE-OT-")
    assert created["customer"]["name"] == "Cliente Solar"
    assert current_stock == Decimal("4.00")
    assert len(movements) == 1 and movements[0].movement_type == "out" and movements[0].quantity == Decimal("8.00")
    assert len(cash_movements) == 1 and cash_movements[0].amount == Decimal("105000.00")
    assert current_cash == Decimal("305000.00")
    assert error.value.status_code == 409


def test_credit_sale_creates_receivable_without_changing_cash(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente Crédito")
        quote = Quote(folio="AE-Q-2", customer_id="", panel_count=6, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 5 kW", payment_method="Financiamiento", panel_subtotal=50000,
            structure_cost=9000, inverter_cost=12000, total=71000, status="accepted", pricing_approved=True)
        account = FinancialAccount(name="Caja", account_type="cash", opening_balance=1000, opening_balance_date=date.today())
        item = InventoryItem(name="Inversor", unit="pza", quantity=2, minimum_quantity=1, unit_cost=8000)
        db.add_all([customer, account, item]); db.flush(); quote.customer_id = customer.id
        db.add(quote); db.commit(); db.refresh(quote); db.refresh(item)

        created = create_sale(SaleInput(quote_id=quote.id, sale_type="credit", due_date=date.today(),
            lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=1)]), identity, db)
        receivable = db.scalars(select(Receivable).where(Receivable.quote_id == quote.id)).one()
        cash_balance = list_financial_accounts(db)[0]["current_balance"]

    assert created["sale_type"] == "credit"
    assert receivable.amount == Decimal("71000.00") and receivable.paid_amount == Decimal("0.00")
    assert cash_balance == Decimal("1000.00")
