from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, CashMovement, FinancialAccount, InventoryItem, InventoryMovement, Purchase, PurchaseCorrection, Supplier, SupplierPayment
from app.product_api import PaymentCorrectionInput, PurchaseInput, PurchaseLineInput, SupplierPaymentInput, add_supplier_payment, create_purchase, list_financial_accounts, list_purchases, list_suppliers, reverse_cash_movement, reverse_purchase, reverse_supplier_payment
from gm_auth.models import AuthIdentity


def test_credit_purchase_receives_stock_creates_payable_and_reduces_bank_on_payment() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), frozenset(), "conta@example.com", "Contabilidad")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor Solar", payment_terms="credit", credit_days=15)
        item = InventoryItem(name="Panel 600 W", unit="pza", quantity=4, minimum_quantity=1, unit_cost=900)
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=3000, opening_balance_date=date.today())
        db.add_all([supplier, item, account]); db.commit(); db.refresh(supplier); db.refresh(item); db.refresh(account)

        created = create_purchase(PurchaseInput(
            supplier_id=supplier.id,
            payment_terms="credit",
            purchase_date=date(2026, 11, 1),
            lines=[PurchaseLineInput(item_id=item.id, quantity=2, unit_cost=Decimal("1000"))],
            initial_payment=Decimal("200"),
            payment_account_id=account.id,
        ), identity, db)
        purchase = db.get(Purchase, created["id"])
        refreshed_item = db.get(InventoryItem, item.id)
        first_balance = list_suppliers(db)[0]["current_balance"]
        movements = db.scalars(select(InventoryMovement).where(InventoryMovement.item_id == item.id)).all()
        movement_type = movements[0].movement_type
        movement_line_id = movements[0].purchase_line_id
        stock_quantity = refreshed_item.quantity
        stock_unit_cost = refreshed_item.unit_cost

        updated = add_supplier_payment(purchase.id, SupplierPaymentInput(amount=Decimal("1800"), account_id=account.id, paid_on=date.today()), identity, db)
        final_supplier_balance = list_suppliers(db)[0]["current_balance"]
        final_bank_balance = list_financial_accounts(db)[0]["current_balance"]
        cash_moves = db.scalars(select(CashMovement).where(CashMovement.source_type == "supplier_payment")).all()
        cash_amounts = [Decimal(row.amount) for row in cash_moves]
        purchase_status = updated["status"]

    assert created["total"] == Decimal("2000.00")
    assert created["balance"] == Decimal("1800.00")
    assert created["due_date"] == date(2026, 11, 16)
    assert purchase_status == "paid"
    assert stock_quantity == Decimal("6.00")
    assert stock_unit_cost == Decimal("1000.00")
    assert movement_type == "purchase" and movement_line_id
    assert first_balance == Decimal("1800.00")
    assert updated["balance"] == Decimal("0.00")
    assert final_supplier_balance == Decimal("0.00")
    assert final_bank_balance == Decimal("1000.00")  # The initial balance remains immutable; linked payments determine current balance.
    assert len(cash_amounts) == 2
    assert sum(cash_amounts) == Decimal("2000.00")


def test_cash_purchase_requires_full_payment_and_credit_terms() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), frozenset(), "conta@example.com", "Contabilidad")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor contado", payment_terms="cash", credit_days=0)
        item = InventoryItem(name="Inversor", unit="pza", quantity=0, minimum_quantity=0, unit_cost=0)
        db.add_all([supplier, item]); db.commit(); db.refresh(supplier); db.refresh(item)
        with pytest.raises(HTTPException) as error:
            create_purchase(PurchaseInput(
                supplier_id=supplier.id,
                payment_terms="cash",
                lines=[PurchaseLineInput(item_id=item.id, quantity=1, unit_cost=100)],
            ), identity, db)

    assert error.value.status_code == 422
    assert "de contado" in error.value.detail


def test_reversing_supplier_payment_keeps_history_and_restores_payable_and_account() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), frozenset(), "conta@example.com", "Contabilidad")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor Solar", payment_terms="credit", credit_days=15)
        item = InventoryItem(name="Panel 600 W", unit="pza", quantity=0, minimum_quantity=0, unit_cost=0)
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=3000, opening_balance_date=date.today())
        db.add_all([supplier, item, account]); db.commit(); db.refresh(supplier); db.refresh(item); db.refresh(account)
        created = create_purchase(PurchaseInput(
            supplier_id=supplier.id, payment_terms="credit", purchase_date=date.today(),
            lines=[PurchaseLineInput(item_id=item.id, quantity=2, unit_cost=1000)],
            initial_payment=Decimal("500"), payment_account_id=account.id,
        ), identity, db)
        purchase = db.get(Purchase, created["id"])
        original_payment = db.scalars(select(SupplierPayment).where(SupplierPayment.purchase_id == purchase.id)).one()

        corrected = reverse_supplier_payment(
            purchase.id, original_payment.id,
            PaymentCorrectionInput(reason="Referencia bancaria capturada incorrectamente"), identity, db,
        )
        movements = db.scalars(select(CashMovement).where(CashMovement.account_id == account.id).order_by(CashMovement.created_at)).all()
        payment_rows = db.scalars(select(SupplierPayment).where(SupplierPayment.purchase_id == purchase.id)).all()
        supplier_balance = list_suppliers(db)[0]["current_balance"]
        bank_balance = list_financial_accounts(db)[0]["current_balance"]

        with pytest.raises(HTTPException) as duplicate:
            reverse_supplier_payment(purchase.id, original_payment.id, PaymentCorrectionInput(reason="Duplicado"), identity, db)
        with pytest.raises(HTTPException) as isolated_cash_reverse:
            reverse_cash_movement(movements[0].id, PaymentCorrectionInput(reason="Debe corregirse como pago"), identity, db)

    assert corrected["paid_amount"] == Decimal("0.00")
    assert corrected["balance"] == Decimal("2000.00")
    assert corrected["status"] == "open"
    assert supplier_balance == Decimal("2000.00")
    assert bank_balance == Decimal("3000.00")
    assert len(payment_rows) == len(movements) == 2
    assert payment_rows[1].reversal_of_id == original_payment.id
    assert movements[1].reversal_of_id == movements[0].id
    assert duplicate.value.status_code == isolated_cash_reverse.value.status_code == 409


def test_purchase_correction_restores_stock_cost_and_supplier_balance_after_payment_reversal() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), frozenset(), "conta@example.com", "Contabilidad")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor Solar", payment_terms="credit", credit_days=15)
        item = InventoryItem(name="Panel 600 W", unit="pza", quantity=4, minimum_quantity=1, unit_cost=900)
        account = FinancialAccount(name="Banco", account_type="bank", opening_balance=3000, opening_balance_date=date.today())
        db.add_all([supplier, item, account]); db.commit(); db.refresh(supplier); db.refresh(item); db.refresh(account)
        created = create_purchase(PurchaseInput(
            supplier_id=supplier.id, payment_terms="credit", purchase_date=date.today(),
            lines=[PurchaseLineInput(item_id=item.id, quantity=2, unit_cost=1000)],
            initial_payment=Decimal("500"), payment_account_id=account.id,
        ), identity, db)
        original = db.scalars(select(SupplierPayment).where(SupplierPayment.purchase_id == created["id"])).one()
        with pytest.raises(HTTPException) as active_payment:
            reverse_purchase(created["id"], PaymentCorrectionInput(reason="Compra duplicada"), identity, db)
        payment_reversal = reverse_supplier_payment(created["id"], original.id,
            PaymentCorrectionInput(reason="Pago capturado por error"), identity, db)
        corrected = reverse_purchase(created["id"], PaymentCorrectionInput(reason="Factura duplicada"), identity, db)
        purchase = db.get(Purchase, created["id"])
        correction = db.scalars(select(PurchaseCorrection).where(PurchaseCorrection.purchase_id == created["id"])).one()
        movements = db.scalars(select(InventoryMovement).where(InventoryMovement.item_id == item.id).order_by(InventoryMovement.created_at)).all()
        supplier_balance = list_suppliers(db)[0]["current_balance"]
        bank_balance = list_financial_accounts(db)[0]["current_balance"]
        stock = db.get(InventoryItem, item.id)
        with pytest.raises(HTTPException) as duplicate:
            reverse_purchase(created["id"], PaymentCorrectionInput(reason="Duplicado"), identity, db)
        with pytest.raises(HTTPException) as late_payment:
            add_supplier_payment(created["id"], SupplierPaymentInput(amount=Decimal("1"), account_id=account.id), identity, db)

    assert active_payment.value.status_code == 409
    assert payment_reversal["paid_amount"] == Decimal("0.00")
    assert corrected["status"] == "corrected" and corrected["balance"] == Decimal("0.00")
    assert corrected["correction"]["reason"] == "Factura duplicada"
    assert correction.amount == Decimal("2000.00")
    assert purchase is not None and purchase.total == Decimal("2000.00")
    assert [movement.movement_type for movement in movements] == ["purchase", "purchase_reversal"]
    assert movements[1].related_movement_id == movements[0].id
    assert stock is not None and stock.quantity == Decimal("4.00") and stock.unit_cost == Decimal("900.00")
    assert supplier_balance == Decimal("0.00") and bank_balance == Decimal("3000.00")
    assert duplicate.value.status_code == late_payment.value.status_code == 409


def test_purchase_correction_is_blocked_after_stock_movement() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), frozenset(), "conta@example.com", "Contabilidad")
    with Session(engine) as db:
        supplier = Supplier(name="Proveedor Solar", payment_terms="credit", credit_days=15)
        item = InventoryItem(name="Panel", unit="pza", quantity=10, unit_cost=800)
        db.add_all([supplier, item]); db.commit(); db.refresh(supplier); db.refresh(item)
        purchase = create_purchase(PurchaseInput(supplier_id=supplier.id, payment_terms="credit", purchase_date=date.today(),
            lines=[PurchaseLineInput(item_id=item.id, quantity=2, unit_cost=1000)]), identity, db)
        db.add(InventoryMovement(item_id=item.id, quantity=1, movement_type="consumption", unit_cost=1000,
            reason="Material utilizado", created_by="instalador"))
        item.quantity = Decimal("11.00"); db.commit()
        with pytest.raises(HTTPException) as error:
            reverse_purchase(purchase["id"], PaymentCorrectionInput(reason="Compra equivocada"), identity, db)
        assert db.scalar(select(PurchaseCorrection.id).where(PurchaseCorrection.purchase_id == purchase["id"])) is None
        assert db.get(InventoryItem, item.id).quantity == Decimal("11.00")

    assert error.value.status_code == 409
