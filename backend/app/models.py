from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, UniqueConstraint
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Quote(Base):
    __tablename__ = "ae_quotes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    folio: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    panel_count: Mapped[int] = mapped_column(Integer, nullable=False)
    panel_brand: Mapped[str] = mapped_column(String(100), default="Jinko")
    panel_watts: Mapped[int] = mapped_column(Integer, default=610)
    inverter: Mapped[str] = mapped_column(String(120), default="Growatt 5 kW")
    payment_method: Mapped[str] = mapped_column(String(60), default="Contado")
    panel_subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    structure_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    inverter_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class FollowUp(Base):
    __tablename__ = "ae_followups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    quote_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Activity(Base):
    __tablename__ = "ae_activities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    kind: Mapped[str] = mapped_column(String(60), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Installation(Base):
    __tablename__ = "ae_installations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    quote_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lead_installer: Mapped[str] = mapped_column(String(180), default="")
    status: Mapped[str] = mapped_column(String(40), default="assigned")
    checklist: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")


class InventoryItem(Base):
    __tablename__ = "ae_inventory"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="pieza")
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    minimum_quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class InventoryMovement(Base):
    __tablename__ = "ae_inventory_movements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    item_id: Mapped[str] = mapped_column(String(36), nullable=False)
    installation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(180), default="")
    created_by: Mapped[str] = mapped_column(String(180), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ProjectExpense(Base):
    __tablename__ = "ae_expenses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    installation_id: Mapped[str] = mapped_column(String(36), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="Viáticos")
    description: Mapped[str] = mapped_column(String(240), default="")
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    receipt_url: Mapped[str] = mapped_column(Text, default="")
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


class IntegrationStatus(Base):
    __tablename__ = "ae_integrations"
    __table_args__ = (UniqueConstraint("provider", name="uq_ae_integration_provider"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(60), nullable=False)
    connected: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(80), default="pending_configuration")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
