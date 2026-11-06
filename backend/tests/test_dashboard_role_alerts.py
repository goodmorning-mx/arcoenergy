from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, FinancialAccount, InventoryItem, Receivable
from app.product_api import dashboard
from app.roles import ROLE_PERMISSIONS


def test_dashboard_returns_permission_scoped_operational_alerts() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        customer = Customer(name="Cliente de prueba")
        db.add(customer); db.flush()
        db.add_all([
            InventoryItem(name="Panel solar", unit="pieza", quantity=2, minimum_quantity=3, unit_cost=4000),
            Receivable(customer_id=customer.id, due_date=date.today(), amount=Decimal("1500"), paid_amount=Decimal("500"), status="pending"),
            FinancialAccount(name="Caja", account_type="cash", opening_balance=Decimal("300")),
        ])
        db.commit()
        admin = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
        marketing = AuthIdentity("marketing", "arcoenergy", frozenset({"marketing"}), ROLE_PERMISSIONS["marketing"], "marketing@example.test", "Marketing")

        full = dashboard(admin, db)
        restricted = dashboard(marketing, db)

    assert full["receivables_open"] == 1000
    assert full["due_receivables"][0]["customer"] == "Cliente de prueba"
    assert full["due_receivables"][0]["status"] == "due"
    assert full["low_stock_items"][0]["available_quantity"] == 2
    assert full["account_balances"][0]["balance"] == 300
    assert restricted["receivables_open"] == 0
    assert restricted["due_receivables"] == []
    assert restricted["low_stock_items"] == []
    assert restricted["account_balances"] == []
