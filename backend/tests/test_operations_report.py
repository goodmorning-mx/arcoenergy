from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from gm_auth.models import AuthIdentity
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, CashMovement, Customer, FinancialAccount, Installation, InventoryItem, InventoryMovement, ProjectExpense, Supplier
from app.product_api import CashTransferInput, create_cash_transfer, operations_report
from app.roles import ROLE_PERMISSIONS


def test_operations_report_summarizes_stock_activity_statuses_and_expenses() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        customer = Customer(name="Cliente operativo", status="active")
        supplier = Supplier(name="Proveedor solar", active=True)
        inactive_supplier = Supplier(name="Proveedor anterior", active=False)
        db.add_all([customer, supplier, inactive_supplier]); db.flush()
        installation = Installation(customer_id=customer.id, folio="AE-OT-REPORT", status="scheduled")
        item = InventoryItem(name="Panel 610 W", category="Módulos", unit="pieza", quantity=10, minimum_quantity=3, unit_cost=Decimal("3500"))
        db.add_all([installation, item]); db.flush()
        db.add_all([
            InventoryMovement(item_id=item.id, installation_id=installation.id, quantity=2, movement_type="out", unit_cost=3500,
                reason="Material para orden", created_at=datetime(2026, 11, 4, tzinfo=timezone.utc)),
            InventoryMovement(item_id=item.id, quantity=5, movement_type="in", unit_cost=3500,
                reason="Compra", created_at=datetime(2026, 10, 28, tzinfo=timezone.utc)),
            ProjectExpense(installation_id=installation.id, category="Viáticos", description="Combustible", amount=Decimal("850"), occurred_on=date(2026, 11, 4)),
            ProjectExpense(installation_id=None, category="Renta", description="Oficina", amount=Decimal("12000"), occurred_on=date(2026, 10, 1)),
        ])
        db.commit()
        accountant = AuthIdentity("accountant", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")

        report = operations_report(from_date=date(2026, 11, 1), to_date=date(2026, 11, 30), identity=accountant, db=db)

    assert report["stock"]["item_count"] == 1
    assert report["stock"]["items"][0]["available_quantity"] == Decimal("10.00")
    assert report["stock"]["items"][0]["unit_cost"] == Decimal("3500.00")
    assert report["stock"]["estimated_value"] == Decimal("35000.00")
    assert report["movements"]["totals_by_type"] == [{"movement_type": "out", "quantity": Decimal("2.00")}]
    assert report["customers_by_status"] == [{"status": "active", "count": 1}]
    assert report["suppliers"] == {"total": 2, "active": 1, "inactive": 1}
    assert report["installations_by_status"] == [{"status": "scheduled", "count": 1}]
    assert report["expenses"]["total"] == Decimal("850.00")
    assert report["expenses"]["by_category"] == [{"category": "Viáticos", "amount": Decimal("850.00")}]


def test_operations_report_hides_inventory_costs_without_cost_permission_and_checks_date_range() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(InventoryItem(name="Panel", quantity=1, unit_cost=Decimal("1000")))
        db.commit()
        installer = AuthIdentity("field", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Instalador")
        report = operations_report(identity=installer, db=db)
        with pytest.raises(HTTPException) as invalid:
            operations_report(from_date=date(2026, 11, 2), to_date=date(2026, 11, 1), identity=installer, db=db)

    assert report["stock"]["estimated_value"] is None
    assert "unit_cost" not in report["stock"]["items"][0]
    assert invalid.value.status_code == 422
    assert report["cash_flow"] is None


def test_operations_report_calculates_period_cash_flow_from_active_account_movements():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        account = FinancialAccount(name="Caja", account_type="cash", opening_balance=1000,
            opening_balance_date=date(2026, 10, 1), active=True)
        opening_in_period = FinancialAccount(name="Banco nuevo", account_type="bank", opening_balance=200,
            opening_balance_date=date(2026, 11, 15), active=True)
        inactive = FinancialAccount(name="Cuenta cerrada", account_type="bank", opening_balance=9000,
            opening_balance_date=date(2026, 1, 1), active=False)
        db.add_all([account, opening_in_period, inactive]); db.flush()
        db.add_all([
            CashMovement(account_id=account.id, direction="in", amount=200, category="Venta", description="Anterior", occurred_on=date(2026, 10, 10)),
            CashMovement(account_id=account.id, direction="out", amount=50, category="Compra", description="Anterior", occurred_on=date(2026, 10, 15)),
            CashMovement(account_id=account.id, direction="in", amount=500, category="Venta", description="Periodo", occurred_on=date(2026, 11, 5)),
            CashMovement(account_id=account.id, direction="out", amount=300, category="Gasto", description="Periodo", occurred_on=date(2026, 11, 10)),
            CashMovement(account_id=opening_in_period.id, direction="out", amount=50, category="Gasto", description="Periodo", occurred_on=date(2026, 11, 20)),
        ])
        db.commit()
        accountant = AuthIdentity("accountant", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
        report = operations_report(from_date=date(2026, 11, 1), to_date=date(2026, 11, 30), identity=accountant, db=db)

    flow = report["cash_flow"]
    assert flow["opening_balance"] == Decimal("1150.00")
    assert flow["opening_entries"] == Decimal("200.00")
    assert flow["inflows"] == Decimal("500.00")
    assert flow["outflows"] == Decimal("350.00")
    assert flow["closing_balance"] == Decimal("1500.00")
    assert {row["name"] for row in flow["accounts"]} == {"Caja", "Banco nuevo"}
    assert next(row for row in flow["accounts"] if row["name"] == "Banco nuevo")["closing_balance"] == Decimal("150.00")


def test_operations_report_separates_internal_transfers_from_cash_inflows_and_outflows():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        cash = FinancialAccount(name="Caja", account_type="cash", opening_balance=1000, opening_balance_date=date(2026, 10, 1))
        bank = FinancialAccount(name="Banco", account_type="bank", opening_balance=200, opening_balance_date=date(2026, 10, 1))
        db.add_all([cash, bank]); db.commit(); db.refresh(cash); db.refresh(bank)
        identity = AuthIdentity("accountant", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")
        create_cash_transfer(CashTransferInput(
            source_account_id=cash.id, destination_account_id=bank.id, amount=Decimal("250"),
            description="Depósito", occurred_on=date(2026, 11, 5),
        ), identity, db)
        report = operations_report(from_date=date(2026, 11, 1), to_date=date(2026, 11, 30), identity=identity, db=db)

    flow = report["cash_flow"]
    assert flow["inflows"] == Decimal("0")
    assert flow["outflows"] == Decimal("0")
    assert flow["transfers_in"] == flow["transfers_out"] == Decimal("250.00")
    assert flow["closing_balance"] == Decimal("1200.00")
    cash_row = next(row for row in flow["accounts"] if row["name"] == "Caja")
    bank_row = next(row for row in flow["accounts"] if row["name"] == "Banco")
    assert cash_row["transfers_out"] == Decimal("250.00") and cash_row["closing_balance"] == Decimal("750.00")
    assert bank_row["transfers_in"] == Decimal("250.00") and bank_row["closing_balance"] == Decimal("450.00")
