from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Customer, Installation, InventoryMovement, ProjectExpense, Quote, Sale
from app.product_api import profitability_report


def test_monthly_project_report_uses_sales_consumption_events_and_project_expenses() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        customer = Customer(name="Cliente real", city="Tampico")
        db.add(customer); db.flush()
        quote = Quote(folio="AE-Q-RPT", customer_id=customer.id, panel_count=8, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor", payment_method="Contado", panel_subtotal=80000,
            structure_cost=10000, inverter_cost=10000, total=100000, status="accepted", pricing_approved=True)
        db.add(quote); db.flush()
        installation = Installation(folio="AE-OT-RPT", customer_id=customer.id, quote_id=quote.id, lead_installer="field@example.test")
        db.add(installation); db.flush()
        db.add(Sale(folio="AE-V-RPT", customer_id=customer.id, quote_id=quote.id, installation_id=installation.id,
            sale_type="cash", total=100000, created_at=datetime(2026, 11, 3, tzinfo=timezone.utc)))
        db.add_all([
            InventoryMovement(item_id="item-a", installation_id=installation.id, quantity=5, movement_type="consumption", unit_cost=2000,
                reason="Consumo instalado", created_at=datetime(2026, 11, 4, tzinfo=timezone.utc)),
            InventoryMovement(item_id="item-a", installation_id=installation.id, quantity=1, movement_type="consumption_return", unit_cost=2000,
                reason="Sobrante recuperado", created_at=datetime(2026, 11, 5, tzinfo=timezone.utc)),
            ProjectExpense(installation_id=installation.id, category="Viáticos", expense_type="variable", description="Combustible", amount=5000, occurred_on=date(2026, 11, 5)),
            ProjectExpense(installation_id=None, category="Nómina", expense_type="fixed", description="Gasto operativo", amount=12000, occurred_on=date(2026, 11, 5)),
        ])
        db.commit()

        report = profitability_report(month="2026-11", db=db)
        project_report = profitability_report(installation_id=installation.id, db=db)

    assert report["complete_financial_statement"] is False
    assert report["returns_and_bonifications"] == {"recorded": False, "included": False}
    assert report["totals"]["sales"] == Decimal("100000.00")
    assert report["totals"]["materials_cost"] == Decimal("8000.00")
    assert report["totals"]["expenses"] == Decimal("17000.00")
    assert report["totals"]["expenses_by_type"] == {"fixed": Decimal("12000.00"), "variable": Decimal("5000.00"), "unclassified": Decimal("0")}
    assert report["rows"][0]["expenses_by_type"]["variable"] == Decimal("5000.00")
    assert report["totals"]["preliminary_result"] == Decimal("75000.00")
    assert len(report["rows"]) == 2
    assert project_report["totals"]["expenses"] == Decimal("5000.00")
    assert len(project_report["rows"]) == 1


def test_report_validates_month_and_does_not_treat_missing_material_cost_as_zero() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        with pytest.raises(HTTPException) as invalid:
            profitability_report(month="Nov-2026", db=db)
        customer = Customer(name="Cliente")
        db.add(customer); db.flush()
        installation = Installation(customer_id=customer.id)
        db.add(installation); db.flush()
        db.add(InventoryMovement(item_id="legacy", installation_id=installation.id, quantity=2,
            movement_type="consumption", unit_cost=None, created_at=datetime.now(timezone.utc)))
        db.commit()
        report = profitability_report(installation_id=installation.id, db=db)

    assert invalid.value.status_code == 422
    assert report["totals"]["missing_cost_movements"] == 1
    assert report["totals"]["materials_cost"] is None
    assert report["totals"]["preliminary_result"] is None
