from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, FinancialAccount, Installation, InventoryItem, InventoryMovement, Quote, Receivable
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
            InventoryItem(name="Artículo agotado", unit="pieza", quantity=0, minimum_quantity=1),
            InventoryItem(name="Artículo disponible", unit="pieza", quantity=10, minimum_quantity=2),
            Receivable(customer_id=customer.id, due_date=date.today(), amount=Decimal("1500"), paid_amount=Decimal("500"), status="pending"),
            Receivable(customer_id=customer.id, due_date=date.today() - timedelta(days=1), amount=Decimal("200"), paid_amount=Decimal("0"), status="overdue"),
            FinancialAccount(name="Caja", account_type="cash", opening_balance=Decimal("300")),
            Installation(customer_id=customer.id, status="assigned"),
            Quote(folio="AE-Q-1", customer_id=customer.id, panel_count=8, panel_subtotal=10000, structure_cost=2000,
                  inverter_cost=3000, total=15000, status="draft", pricing_approved=False),
        ])
        today = datetime.now(timezone.utc).date()
        movement_time = datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        db.add_all([
            InventoryMovement(item_id="solar", quantity=2, movement_type="purchase", created_at=movement_time),
            InventoryMovement(item_id="solar", quantity=1, movement_type="return", created_at=movement_time),
            InventoryMovement(item_id="solar", quantity=1, movement_type="out", created_at=movement_time),
            InventoryMovement(item_id="solar", quantity=1, movement_type="consumption", created_at=movement_time),
        ])
        db.commit()
        admin = AuthIdentity("admin", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
        marketing = AuthIdentity("marketing", "arcoenergy", frozenset({"marketing"}), ROLE_PERMISSIONS["marketing"], "marketing@example.test", "Marketing")

        full = dashboard(admin, db)
        restricted = dashboard(marketing, db)

    assert full["receivables_open"] == 1200
    assert full["due_receivables"][0]["customer"] == "Cliente de prueba"
    assert [row["status"] for row in full["due_receivables"]] == ["overdue", "due"]
    assert next(row["available_quantity"] for row in full["low_stock_items"] if row["name"] == "Panel solar") == 2
    assert full["inventory_summary"] == {"total_items": 3, "available_items": 1, "low_stock_items": 1, "out_of_stock_items": 1}
    yesterday = next(row for row in full["inventory_activity_7d"] if row["date"] == (today - timedelta(days=1)).isoformat())
    assert (yesterday["entries"], yesterday["exits"]) == (2, 1)
    assert full["quotes_pending_approval"] == 1
    assert full["receivables_overdue"] == {"count": 1, "amount": 200.0}
    assert full["installations_active"] == 1
    assert full["account_balances"][0]["balance"] == 300
    assert restricted["receivables_open"] == 0
    assert restricted["due_receivables"] == []
    assert restricted["low_stock_items"] == []
    assert restricted["inventory_summary"] == {"total_items": 0, "available_items": 0, "low_stock_items": 0, "out_of_stock_items": 0}
    assert restricted["inventory_activity_7d"] == []
    assert restricted["installations_active"] == 0
    assert restricted["quotes_pending_approval"] == 1
    assert restricted["receivables_overdue"] == {"count": 0, "amount": 0.0}
    assert restricted["account_balances"] == []
