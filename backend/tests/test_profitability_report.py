from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, CashMovement, Customer, Installation, InventoryMovement, ProfitabilityAdjustment, Project, ProjectExpense, Quote, Sale
from app.product_api import PaymentCorrectionInput, list_profitability_adjustments, profitability_report, reverse_profitability_adjustment


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
            ProfitabilityAdjustment(installation_id=installation.id, adjustment_type="bonification", description="Bonificación autorizada", amount=2000, occurred_on=date(2026, 11, 6)),
        ])
        db.commit()

        report = profitability_report(month="2026-11", db=db)
        project_report = profitability_report(installation_id=installation.id, db=db)
        adjustment = db.scalar(select(ProfitabilityAdjustment).where(ProfitabilityAdjustment.adjustment_type == "bonification"))
        reversal = reverse_profitability_adjustment(adjustment.id, PaymentCorrectionInput(reason="Importe capturado incorrectamente"), identity=type("Identity", (), {"email": "contador@arcoenergy.mx"})(), db=db)
        corrected = profitability_report(installation_id=installation.id, db=db)
        assert reversal["amount"] == -Decimal("2000.00")
        assert corrected["totals"]["returns_and_bonifications"] == Decimal("0.00")
        assert db.query(CashMovement).count() == 0

    assert report["complete_financial_statement"] is False
    assert report["returns_and_bonifications"] == {"recorded": True, "included": True, "total": Decimal("2000.00")}
    assert report["totals"]["sales"] == Decimal("100000.00")
    assert report["totals"]["materials_cost"] == Decimal("8000.00")
    assert report["totals"]["expenses"] == Decimal("17000.00")
    assert report["totals"]["expenses_by_type"] == {"fixed": Decimal("12000.00"), "variable": Decimal("5000.00"), "unclassified": Decimal("0")}
    assert report["rows"][0]["expenses_by_type"]["variable"] == Decimal("5000.00")
    assert report["totals"]["returns_and_bonifications"] == Decimal("2000.00")
    assert report["totals"]["adjustments_by_type"] == {"return": Decimal("0"), "bonification": Decimal("2000.00")}
    assert report["totals"]["preliminary_result"] == Decimal("77000.00")
    assert len(report["rows"]) == 2
    assert project_report["totals"]["expenses"] == Decimal("5000.00")
    assert project_report["totals"]["preliminary_result"] == Decimal("89000.00")
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


def test_project_report_and_adjustment_agenda_filter_by_project_across_work_orders() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        customer = Customer(name="Cliente proyecto", city="Tampico")
        other_customer = Customer(name="Otro cliente", city="Altamira")
        db.add_all([customer, other_customer]); db.flush()
        project = Project(code="AE-P-TEST-1", customer_id=customer.id, name="Proyecto multiorden")
        other_project = Project(code="AE-P-TEST-2", customer_id=other_customer.id, name="Otro proyecto")
        db.add_all([project, other_project]); db.flush()
        first_order = Installation(customer_id=customer.id, project_id=project.id, folio="AE-OT-P-1")
        second_order = Installation(customer_id=customer.id, project_id=project.id, folio="AE-OT-P-2")
        other_order = Installation(customer_id=other_customer.id, project_id=other_project.id, folio="AE-OT-P-3")
        db.add_all([first_order, second_order, other_order]); db.flush()
        db.add_all([
            ProfitabilityAdjustment(installation_id=first_order.id, adjustment_type="return", description="Ajuste uno", amount=100, occurred_on=date(2026, 11, 2)),
            ProfitabilityAdjustment(installation_id=second_order.id, adjustment_type="bonification", description="Ajuste dos", amount=200, occurred_on=date(2026, 11, 3)),
            ProfitabilityAdjustment(installation_id=other_order.id, adjustment_type="return", description="Otro proyecto", amount=900, occurred_on=date(2026, 11, 3)),
        ])
        db.commit()

        report = profitability_report(month="2026-11", project_id=project.id, db=db)
        adjustments = list_profitability_adjustments(month="2026-11", project_id=project.id, db=db)

    assert len(report["rows"]) == 1
    assert report["rows"][0]["project_id"] == project.id
    assert report["totals"]["returns_and_bonifications"] == Decimal("300.00")
    assert len(adjustments) == 2
    assert {row["description"] for row in adjustments} == {"Ajuste uno", "Ajuste dos"}
