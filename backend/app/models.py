from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "ae_customers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(180), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="lead")
    source: Mapped[str] = mapped_column(String(40), default="crm")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class QuotePackage(Base):
    __tablename__ = "ae_quote_packages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    panel_count: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    panel_brand: Mapped[str] = mapped_column(String(100), default="")
    panel_watts: Mapped[int] = mapped_column(Integer, default=0)
    panel_unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    structure_name: Mapped[str] = mapped_column(String(120), default="Estructura")
    structure_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    inverter_options: Mapped[list] = mapped_column(JSON, default=list)
    default_inverter: Mapped[str] = mapped_column(String(120), default="")
    payment_methods: Mapped[list] = mapped_column(JSON, default=lambda: ["Contado", "Financiamiento", "Plan 24"])
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pricing_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[str] = mapped_column(String(180), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class Quote(Base):
    __tablename__ = "ae_quotes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    folio: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    installation_address: Mapped[str] = mapped_column(Text, default="")
    installation_city: Mapped[str] = mapped_column(String(120), default="")
    panel_count: Mapped[int] = mapped_column(Integer, nullable=False)
    panel_brand: Mapped[str] = mapped_column(String(100), default="Jinko")
    panel_watts: Mapped[int] = mapped_column(Integer, default=610)
    structure_name: Mapped[str] = mapped_column(String(120), default="Estructura")
    inverter: Mapped[str] = mapped_column(String(120), default="Growatt 5 kW")
    payment_method: Mapped[str] = mapped_column(String(60), default="Contado")
    panel_subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    structure_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    inverter_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    pricing_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    drive_file_id: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class FollowUp(Base):
    __tablename__ = "ae_followups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    quote_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    assigned_to: Mapped[str] = mapped_column(String(180), default="")
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    push_claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    push_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Activity(Base):
    __tablename__ = "ae_activities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    kind: Mapped[str] = mapped_column(String(60), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Project(Base):
    __tablename__ = "ae_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("ae_customers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Installation(Base):
    __tablename__ = "ae_installations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    folio: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("ae_projects.id"), nullable=True, index=True)
    quote_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lead_installer: Mapped[str] = mapped_column(String(180), default="")
    status: Mapped[str] = mapped_column(String(40), default="assigned")
    checklist: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    material_request_drive_file_id: Mapped[str] = mapped_column(String(200), default="")
    material_request_filename: Mapped[str] = mapped_column(String(255), default="")
    material_request_content_type: Mapped[str] = mapped_column(String(100), default="")
    material_request_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InstallationAssignment(Base):
    __tablename__ = "ae_installation_assignments"
    __table_args__ = (UniqueConstraint("installation_id", "installer_email", name="uq_ae_installation_assignment_email"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    installation_id: Mapped[str] = mapped_column(ForeignKey("ae_installations.id", ondelete="CASCADE"), nullable=False, index=True)
    installer_email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    assigned_by: Mapped[str] = mapped_column(String(180), default="")
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PushSubscription(Base):
    __tablename__ = "ae_push_subscriptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(200), nullable=False)
    auth: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Sale(Base):
    __tablename__ = "ae_sales"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    folio: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("ae_customers.id"), nullable=False, index=True)
    quote_id: Mapped[str] = mapped_column(ForeignKey("ae_quotes.id"), nullable=False, unique=True)
    installation_id: Mapped[str] = mapped_column(ForeignKey("ae_installations.id"), nullable=False, unique=True)
    sale_type: Mapped[str] = mapped_column(String(20), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class SaleCorrection(Base):
    __tablename__ = "ae_sale_corrections"
    __table_args__ = (
        UniqueConstraint("sale_id", name="uq_ae_sale_correction_sale"),
        UniqueConstraint("cash_movement_id", name="uq_ae_sale_correction_cash_movement"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    sale_id: Mapped[str] = mapped_column(ForeignKey("ae_sales.id"), nullable=False)
    cash_movement_id: Mapped[str | None] = mapped_column(ForeignKey("ae_cash_movements.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class WorkOrderMaterial(Base):
    __tablename__ = "ae_work_order_materials"
    __table_args__ = (UniqueConstraint("installation_id", "item_id", name="uq_ae_work_order_material_item"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    installation_id: Mapped[str] = mapped_column(ForeignKey("ae_installations.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("ae_inventory.id"), nullable=False, index=True)
    requested_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    preissued_quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    consumed_quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class InventoryItem(Base):
    __tablename__ = "ae_inventory"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    brand: Mapped[str] = mapped_column(String(100), default="")
    model: Mapped[str] = mapped_column(String(120), default="")
    supplier_id: Mapped[str | None] = mapped_column(ForeignKey("ae_suppliers.id"), nullable=True, index=True)
    barcode: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    unit: Mapped[str] = mapped_column(String(40), default="pieza")
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    minimum_quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    restock_responsible_email: Mapped[str] = mapped_column(String(180), default="")
    low_stock_alert_active: Mapped[bool] = mapped_column(Boolean, default=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class InventoryMovement(Base):
    __tablename__ = "ae_inventory_movements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    installation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), default="in", nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    related_movement_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    purchase_line_id: Mapped[str | None] = mapped_column(ForeignKey("ae_purchase_lines.id"), nullable=True, index=True)
    work_order_material_id: Mapped[str | None] = mapped_column(ForeignKey("ae_work_order_materials.id", name="fk_ae_inv_movements_work_order_material"), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(String(180), default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class OfflineOperation(Base):
    """Server receipt for client-generated IDs on retryable field writes."""
    __tablename__ = "ae_offline_operations"
    __table_args__ = (UniqueConstraint("owner_email", "operation_id", name="uq_ae_offline_operation_owner_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_email: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    operation_id: Mapped[str] = mapped_column(String(80), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class ProjectExpense(Base):
    __tablename__ = "ae_expenses"
    __table_args__ = (UniqueConstraint("reversal_of_id", name="uq_ae_expenses_reversal"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    installation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("ae_projects.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(80), default="Viáticos")
    expense_type: Mapped[str] = mapped_column(String(20), default="unclassified", nullable=False)
    description: Mapped[str] = mapped_column(String(240), default="")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    receipt_url: Mapped[str] = mapped_column(Text, default="")
    receipt_drive_file_id: Mapped[str] = mapped_column(String(200), default="")
    receipt_filename: Mapped[str] = mapped_column(String(255), default="")
    receipt_content_type: Mapped[str] = mapped_column(String(100), default="")
    receipt_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    account_id: Mapped[str | None] = mapped_column(ForeignKey("ae_financial_accounts.id"), nullable=True, index=True)
    reversal_of_id: Mapped[str | None] = mapped_column(ForeignKey("ae_expenses.id"), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ProfitabilityAdjustment(Base):
    """Append-only project return/bonification entries for preliminary reporting."""
    __tablename__ = "ae_profitability_adjustments"
    __table_args__ = (UniqueConstraint("reversal_of_id", name="uq_ae_profitability_adjustment_reversal"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    installation_id: Mapped[str | None] = mapped_column(ForeignKey("ae_installations.id"), nullable=True, index=True)
    adjustment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(240), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    reversal_of_id: Mapped[str | None] = mapped_column(ForeignKey("ae_profitability_adjustments.id"), nullable=True, index=True)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class FinancialAccount(Base):
    __tablename__ = "ae_financial_accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    opening_balance: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    opening_balance_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class CashMovement(Base):
    __tablename__ = "ae_cash_movements"
    __table_args__ = (UniqueConstraint("reversal_of_id", name="uq_ae_cash_movement_reversal"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    account_id: Mapped[str] = mapped_column(ForeignKey("ae_financial_accounts.id"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    occurred_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), default="manual", nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reversal_of_id: Mapped[str | None] = mapped_column(ForeignKey("ae_cash_movements.id"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Supplier(Base):
    __tablename__ = "ae_suppliers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    rfc: Mapped[str] = mapped_column(String(20), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(180), default="")
    payment_terms: Mapped[str] = mapped_column(String(20), default="cash", nullable=False)
    credit_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Purchase(Base):
    __tablename__ = "ae_purchases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    folio: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("ae_suppliers.id"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), default="")
    invoice_drive_file_id: Mapped[str] = mapped_column(String(200), default="")
    invoice_filename: Mapped[str] = mapped_column(String(255), default="")
    invoice_content_type: Mapped[str] = mapped_column(String(100), default="")
    invoice_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_terms: Mapped[str] = mapped_column(String(20), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PurchaseCorrection(Base):
    __tablename__ = "ae_purchase_corrections"
    __table_args__ = (UniqueConstraint("purchase_id", name="uq_ae_purchase_correction_purchase"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    purchase_id: Mapped[str] = mapped_column(ForeignKey("ae_purchases.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PurchaseLine(Base):
    __tablename__ = "ae_purchase_lines"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    purchase_id: Mapped[str] = mapped_column(ForeignKey("ae_purchases.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("ae_inventory.id"), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    previous_unit_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)


class SupplierPayment(Base):
    __tablename__ = "ae_supplier_payments"
    __table_args__ = (
        UniqueConstraint("reversal_of_id", name="uq_ae_supplier_payment_reversal"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    purchase_id: Mapped[str] = mapped_column(ForeignKey("ae_purchases.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("ae_financial_accounts.id"), nullable=False, index=True)
    cash_movement_id: Mapped[str] = mapped_column(ForeignKey("ae_cash_movements.id"), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    reference: Mapped[str] = mapped_column(String(180), default="")
    reversal_of_id: Mapped[str | None] = mapped_column(ForeignKey("ae_supplier_payments.id", name="fk_ae_supplier_payment_reversal"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Receivable(Base):
    __tablename__ = "ae_receivables"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    quote_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    installment_number: Mapped[int] = mapped_column(Integer, default=1)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    payment_method: Mapped[str] = mapped_column(String(60), default="Transferencia")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class CustomerPayment(Base):
    __tablename__ = "ae_customer_payments"
    __table_args__ = (
        UniqueConstraint("reversal_of_id", name="uq_ae_customer_payment_reversal"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    receivable_id: Mapped[str] = mapped_column(ForeignKey("ae_receivables.id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("ae_financial_accounts.id"), nullable=False, index=True)
    cash_movement_id: Mapped[str] = mapped_column(ForeignKey("ae_cash_movements.id"), unique=True, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    reference: Mapped[str] = mapped_column(String(180), default="")
    reversal_of_id: Mapped[str | None] = mapped_column(ForeignKey("ae_customer_payments.id", name="fk_ae_customer_payment_reversal"), nullable=True)
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class IntegrationStatus(Base):
    __tablename__ = "ae_integrations"
    __table_args__ = (UniqueConstraint("provider", name="uq_ae_integration_provider"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(80), default="pending_configuration")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class HistoryCard(Base):
    """Append-only record of a user story observation and its source."""
    __tablename__ = "ae_history_cards"
    __table_args__ = (UniqueConstraint("story_id", "version", name="uq_ae_history_card_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    story_id: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    iteration: Mapped[str] = mapped_column(String(80), nullable=False)
    stakeholder: Mapped[str] = mapped_column(String(180), nullable=False)
    source_literal: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_reference: Mapped[str] = mapped_column(Text, default="")
    source_artifact: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    source_language: Mapped[str | None] = mapped_column(String(20), default="es", nullable=True)
    source_attribution: Mapped[str | None] = mapped_column(String(180), default="", nullable=True)
    source_occurred_at: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_confidence: Mapped[str | None] = mapped_column(String(40), default="unverified_reconstruction", nullable=True)
    source_links: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)
    normalized_story: Mapped[str] = mapped_column(Text, nullable=False)
    acceptance_criteria: Mapped[list] = mapped_column(JSON, default=list)
    unresolved_questions: Mapped[list] = mapped_column(JSON, default=list)
    linked_cards: Mapped[list] = mapped_column(JSON, default=list)
    recorded_by: Mapped[str] = mapped_column(String(180), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
