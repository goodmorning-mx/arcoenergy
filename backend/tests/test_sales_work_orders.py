from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity, memberships, users

from app.models import Activity, Base, CashMovement, Customer, FinancialAccount, Installation, InventoryItem, InventoryMovement, OfflineOperation, ProjectExpense, Quote, Receivable, Sale, SaleCorrection, WorkOrderMaterial
from app.product_api import ExpenseInput, InventoryReturnInput, PaymentCorrectionInput, PaymentInput, SaleInput, SaleMaterialInput, StockInput, _installment_due_date, add_expense, consume_inventory, create_sale, list_financial_accounts, list_inventory, list_receivables, profitability_report, record_payment, return_inventory, reverse_cash_sale
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


def test_cash_sale_creates_folio_work_order_material_reservation_and_cash_inflow(monkeypatch) -> None:
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
        material = db.scalars(select(WorkOrderMaterial).where(WorkOrderMaterial.installation_id == order.id)).one()
        sale = db.get(Sale, created["id"])
        cash_movements = db.scalars(select(CashMovement).where(CashMovement.source_type == "sale")).all()
        current_cash = list_financial_accounts(db)[0]["current_balance"]
        with pytest.raises(HTTPException) as error:
            create_sale(SaleInput(quote_id=quote.id, sale_type="cash", account_id=account.id,
                lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=1)]), identity, db)

    assert sale.folio.startswith("AE-V-")
    assert order.folio and order.folio.startswith("AE-OT-")
    assert created["customer"]["name"] == "Cliente Solar"
    assert current_stock == Decimal("12.00")
    assert len(movements) == 0
    assert material.requested_quantity == Decimal("8.00") and material.preissued_quantity == Decimal("0.00")
    assert len(cash_movements) == 1 and cash_movements[0].amount == Decimal("105000.00")
    assert current_cash == Decimal("305000.00")
    assert error.value.status_code == 409


def test_installer_consumption_decrements_stock_once_and_cannot_exceed_order(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    installer = AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Campo")
    with Session(engine) as db:
        customer = Customer(name="Cliente Solar")
        quote = Quote(folio="AE-Q-3", customer_id="", panel_count=8, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 5 kW", payment_method="Contado", panel_subtotal=80000,
            structure_cost=10000, inverter_cost=15000, total=105000, status="accepted", pricing_approved=True)
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=0, opening_balance_date=date.today())
        item = InventoryItem(name="Panel 600 W", unit="pza", quantity=12, unit_cost=900)
        db.add_all([customer, account, item]); db.flush(); quote.customer_id = customer.id; db.add(quote); db.commit()
        created = create_sale(SaleInput(quote_id=quote.id, sale_type="cash", account_id=account.id,
            lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=8)]), admin, db)
        consume_payload = StockInput(item_id=item.id, quantity=3, installation_id=created["installation_id"], operation_id="field-consume-cost-test")
        consume_result = consume_inventory(consume_payload, installer, db)
        assert db.get(InventoryItem, item.id).quantity == Decimal("9.00")
        assert consume_result["movement"]["movement_type"] == "consumption"
        assert consume_result["physical_issue"]["movement_type"] == "out"
        assert "unit_cost" not in consume_result["movement"]
        assert "unit_cost" not in consume_result["physical_issue"]
        assert "unit_cost" not in consume_result["item"]
        consume_retry = consume_inventory(consume_payload, installer, db)
        assert "unit_cost" not in consume_retry["movement"]
        assert "unit_cost" not in consume_retry["physical_issue"]
        assert profitability_report(installation_id=created["installation_id"], db=db)["totals"]["materials_cost"] == Decimal("2700.00")
        damage = return_inventory(InventoryReturnInput(out_movement_id=consume_result["physical_issue"]["id"], quantity=1, condition="damaged"), installer, db)
        assert damage["movement"]["movement_type"] == "damage"
        assert db.get(InventoryItem, item.id).quantity == Decimal("9.00")
        assert profitability_report(installation_id=created["installation_id"], db=db)["totals"]["materials_cost"] == Decimal("2700.00")
        return_inventory(InventoryReturnInput(out_movement_id=consume_result["physical_issue"]["id"], quantity=1), installer, db)
        corrected = profitability_report(installation_id=created["installation_id"], db=db)
        assert corrected["totals"]["materials_cost"] == Decimal("1800.00")
        assert db.get(InventoryItem, item.id).quantity == Decimal("10.00")
        with pytest.raises(HTTPException) as error:
            consume_inventory(StockInput(item_id=item.id, quantity=7, installation_id=created["installation_id"]), installer, db)
        assert error.value.status_code == 409
        material = db.scalars(select(WorkOrderMaterial).where(WorkOrderMaterial.installation_id == created["installation_id"])).one()
        assert material.consumed_quantity == Decimal("2.00")
        assert material.preissued_quantity == Decimal("2.00")


def test_installation_material_confirmation_uses_already_issued_stock_without_second_deduction(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Campo")
    with Session(engine) as db:
        customer = Customer(name="Cliente Solar")
        db.add(customer); db.flush()
        installation = Installation(customer_id=customer.id, lead_installer="field@example.test")
        item = InventoryItem(name="Panel", quantity=5, unit_cost=900)
        db.add_all([installation, item]); db.flush()
        material = WorkOrderMaterial(installation_id=installation.id, item_id=item.id, requested_quantity=5,
            preissued_quantity=5, consumed_quantity=0, unit_cost=900)
        db.add(material); db.commit()
        consume_inventory(StockInput(item_id=item.id, quantity=3, installation_id=installation.id), installer, db)
        assert db.get(InventoryItem, item.id).quantity == Decimal("5.00")
        assert db.get(WorkOrderMaterial, material.id).consumed_quantity == Decimal("3.00")


def test_return_of_legacy_issue_is_limited_to_unconsumed_material() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Campo")
    with Session(engine) as db:
        customer = Customer(name="Cliente Solar")
        db.add(customer); db.flush()
        installation = Installation(customer_id=customer.id, lead_installer="field@example.test")
        item = InventoryItem(name="Panel", quantity=5, unit_cost=900)
        db.add_all([installation, item]); db.flush()
        material = WorkOrderMaterial(installation_id=installation.id, item_id=item.id, requested_quantity=5,
            preissued_quantity=5, consumed_quantity=3, unit_cost=900)
        db.add(material); db.flush()
        issue = InventoryMovement(item_id=item.id, installation_id=installation.id, quantity=5, movement_type="out",
            work_order_material_id=material.id, unit_cost=900, reason="Salida de orden", created_by="coordinador")
        db.add(issue); db.commit()
        with pytest.raises(HTTPException) as error:
            return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=3), installer, db)
        assert error.value.status_code == 409
        return_inventory(InventoryReturnInput(out_movement_id=issue.id, quantity=2), installer, db)
        assert db.get(InventoryItem, item.id).quantity == Decimal("7.00")
        assert db.get(WorkOrderMaterial, material.id).preissued_quantity == Decimal("3.00")


def test_retry_of_consumption_and_expense_is_idempotent_and_rejects_reused_payload() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente Solar")
        account = FinancialAccount(name="Caja", account_type="cash", opening_balance=500, opening_balance_date=date.today())
        item = InventoryItem(name="Panel", quantity=10, unit_cost=900)
        db.add_all([customer, account, item]); db.flush()
        installation = Installation(customer_id=customer.id, lead_installer="field@example.test")
        db.add(installation); db.commit()

        payload = StockInput(item_id=item.id, quantity=2, installation_id=installation.id, operation_id="consume-12345678")
        first = consume_inventory(payload, admin, db)
        retry = consume_inventory(payload, admin, db)
        assert first["movement"]["id"] == retry["movement"]["id"]
        assert db.get(InventoryItem, item.id).quantity == Decimal("8.00")
        assert db.query(OfflineOperation).filter_by(operation_id="consume-12345678").count() == 1
        assert db.query(InventoryMovement).filter_by(movement_type="consumption").count() == 1
        return_payload = InventoryReturnInput(out_movement_id=first["physical_issue"]["id"], quantity=0.5,
            operation_id="return-12345678")
        first_return = return_inventory(return_payload, admin, db)
        retry_return = return_inventory(return_payload, admin, db)
        assert first_return["movement"]["id"] == retry_return["movement"]["id"]
        assert db.get(InventoryItem, item.id).quantity == Decimal("8.50")
        assert db.query(InventoryMovement).filter_by(movement_type="return").count() == 1
        with pytest.raises(HTTPException) as conflict:
            consume_inventory(StockInput(item_id=item.id, quantity=1, installation_id=installation.id, operation_id="consume-12345678"), admin, db)
        assert conflict.value.status_code == 409
        assert db.get(InventoryItem, item.id).quantity == Decimal("8.50")

        expense = ExpenseInput(installation_id=installation.id, account_id=account.id, category="Viáticos",
            description="Gasolina de instalación", amount=250, occurred_on=date.today(), operation_id="expense-12345678")
        first_expense = add_expense(expense, admin, db)
        retry_expense = add_expense(expense, admin, db)
        assert first_expense["id"] == retry_expense["id"]
        assert db.query(ProjectExpense).count() == 1
        assert db.query(CashMovement).filter_by(source_type="expense").count() == 1


def test_credit_sale_creates_installment_schedule_without_changing_cash(monkeypatch) -> None:
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

        created = create_sale(SaleInput(quote_id=quote.id, sale_type="credit", due_date=date(2026, 1, 31),
            installment_count=3, installment_frequency="monthly",
            lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=1)]), identity, db)
        corrected = reverse_cash_sale(created["id"], PaymentCorrectionInput(reason="Financiamiento cancelado"), identity, db)
        receivables = db.scalars(select(Receivable).where(Receivable.quote_id == quote.id).order_by(Receivable.installment_number)).all()
        cash_balance = list_financial_accounts(db)[0]["current_balance"]

    assert created["sale_type"] == "credit"
    assert created["installment_count"] == 3
    assert [row.installment_number for row in receivables] == [1, 2, 3]
    assert [row.amount for row in receivables] == [Decimal("23666.66"), Decimal("23666.66"), Decimal("23666.68")]
    assert [row.due_date for row in receivables] == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)]
    assert sum((row.amount for row in receivables), Decimal("0.00")) == Decimal("71000.00")
    assert all(row.paid_amount == Decimal("0.00") for row in receivables)
    assert cash_balance == Decimal("1000.00")
    assert corrected["correction"]["cash_movement_id"] is None
    assert corrected["can_reverse"] is False


def test_preinstallation_cash_sale_correction_restores_cash_and_releases_stock(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente Venta", city="Tampico")
        account = FinancialAccount(name="Banco de ventas", account_type="bank", opening_balance=5000, opening_balance_date=date.today())
        item = InventoryItem(name="Panel 600 W", quantity=10, unit_cost=900)
        quote = Quote(folio="AE-Q-REVERSE", customer_id="", panel_count=8, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 5 kW", payment_method="Contado", panel_subtotal=80000,
            structure_cost=10000, inverter_cost=15000, total=105000, status="accepted", pricing_approved=True)
        db.add_all([customer, account, item]); db.flush(); quote.customer_id = customer.id; db.add(quote); db.commit()
        sale = create_sale(SaleInput(quote_id=quote.id, sale_type="cash", account_id=account.id,
            lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=4)]), admin, db)
        assert sale["can_reverse"] is True
        assert list_inventory(admin, db)[0]["available_quantity"] == Decimal("6.00")

        corrected = reverse_cash_sale(sale["id"], PaymentCorrectionInput(reason="Cliente canceló compra"), admin, db)
        balance = list_financial_accounts(db)[0]["current_balance"]
        inventory = list_inventory(admin, db)[0]
        report = profitability_report(installation_id=sale["installation_id"], db=db)
        original = db.get(Sale, sale["id"])
        movements = db.query(CashMovement).filter(CashMovement.source_id == sale["id"]).all()
        correction = db.query(SaleCorrection).filter_by(sale_id=sale["id"]).one()
        activities = db.query(Activity).filter_by(kind="corrección de venta").all()
        with pytest.raises(HTTPException) as duplicate:
            reverse_cash_sale(sale["id"], PaymentCorrectionInput(reason="Doble captura"), admin, db)

    assert corrected["correction"]["reason"] == "Cliente canceló compra"
    assert corrected["can_reverse"] is False
    assert original is not None and original.total == Decimal("105000.00")
    assert correction.amount == Decimal("105000.00")
    assert correction.cash_movement_id == movements[1].id
    assert movements[1].direction == "out" and movements[1].reversal_of_id == movements[0].id
    assert balance == Decimal("5000.00")
    assert inventory["available_quantity"] == Decimal("10.00")
    assert report["totals"]["sales"] == Decimal("0.00")
    assert len(activities) == 1
    assert duplicate.value.status_code == 409


def test_unpaid_credit_sale_correction_hides_receivables_and_blocks_new_payments(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente Crédito", email="cliente@example.test")
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=0, opening_balance_date=date.today())
        item = InventoryItem(name="Panel 600 W", quantity=10, unit_cost=900)
        quote = Quote(folio="AE-Q-CREDIT-REVERSE", customer_id="", panel_count=8, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 5 kW", payment_method="Financiamiento", panel_subtotal=80000,
            structure_cost=10000, inverter_cost=15000, total=105000, status="accepted", pricing_approved=True)
        db.add_all([customer, account, item]); db.flush(); quote.customer_id = customer.id; db.add(quote); db.commit()
        sale = create_sale(SaleInput(quote_id=quote.id, sale_type="credit", due_date=date.today(), installment_count=3,
            lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=4)]), admin, db)
        installments = db.scalars(select(Receivable).where(Receivable.quote_id == quote.id)).all()
        assert len(list_receivables(db)) == 3

        corrected = reverse_cash_sale(sale["id"], PaymentCorrectionInput(reason="Financiamiento cancelado"), admin, db)
        hidden = list_receivables(db)
        with pytest.raises(HTTPException) as blocked:
            record_payment(installments[0].id, PaymentInput(amount=Decimal("100.00"), account_id=account.id), admin, db)

    assert corrected["correction"]["cash_movement_id"] is None
    assert corrected["can_reverse"] is False
    assert hidden == []
    assert blocked.value.status_code == 409


def test_cash_sale_correction_is_blocked_after_installer_confirmation(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    admin = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    installer = AuthIdentity("installer-1", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Field")
    with Session(engine) as db:
        customer = Customer(name="Cliente Activo")
        account = FinancialAccount(name="Caja", account_type="cash", opening_balance=1000, opening_balance_date=date.today())
        item = InventoryItem(name="Panel", quantity=2, unit_cost=900)
        quote = Quote(folio="AE-Q-CONFIRM", customer_id="", panel_count=4, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 3 kW", payment_method="Contado", panel_subtotal=20000,
            structure_cost=5000, inverter_cost=5000, total=30000, status="accepted", pricing_approved=True)
        db.add_all([customer, account, item]); db.flush(); quote.customer_id = customer.id; db.add(quote); db.commit()
        sale = create_sale(SaleInput(quote_id=quote.id, sale_type="cash", account_id=account.id, lead_installer=installer.email,
            materials=[SaleMaterialInput(item_id=item.id, quantity=1)]), admin, db)
        product_api.confirm_installation_assignment(sale["installation_id"], installer, db)
        with pytest.raises(HTTPException) as error:
            reverse_cash_sale(sale["id"], PaymentCorrectionInput(reason="Venta equivocada"), admin, db)
    assert error.value.status_code == 409


def test_installment_calendar_handles_weekly_and_biweekly_dates() -> None:
    first_due = date(2026, 11, 6)
    assert _installment_due_date(first_due, 2, "weekly") == date(2026, 11, 20)
    assert _installment_due_date(first_due, 2, "biweekly") == date(2026, 12, 4)


def test_credit_sale_rejects_more_installments_than_total_cents(monkeypatch) -> None:
    monkeypatch.setattr(product_api.auth_service, "engine", installer_directory())
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("admin-1", "arcoenergy", frozenset({"administrador"}), ROLE_PERMISSIONS["administrador"], "admin@example.test", "Admin")
    with Session(engine) as db:
        customer = Customer(name="Cliente Crédito")
        quote = Quote(folio="AE-Q-CENTS", customer_id="", panel_count=1, panel_brand="Solar", panel_watts=600,
            structure_name="Fija", inverter="Inversor 5 kW", payment_method="Financiamiento", panel_subtotal=0.02,
            structure_cost=0, inverter_cost=0, total=0.02, status="accepted", pricing_approved=True)
        item = InventoryItem(name="Inversor", unit="pza", quantity=2, unit_cost=0)
        db.add_all([customer, item]); db.flush(); quote.customer_id = customer.id
        db.add(quote); db.commit()
        with pytest.raises(HTTPException) as error:
            create_sale(SaleInput(quote_id=quote.id, sale_type="credit", due_date=date.today(), installment_count=3,
                lead_installer="field@example.test", materials=[SaleMaterialInput(item_id=item.id, quantity=1)]), identity, db)
    assert error.value.status_code == 422
