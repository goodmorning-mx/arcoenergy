from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN
import hashlib
import json
from io import BytesIO
import re
from typing import Literal
from urllib.parse import quote as urlquote, unquote
from uuid import uuid4
import xml.etree.ElementTree as ET

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased, sessionmaker
from gm_agent import AgentService, Conversation, Message, OpenAIProvider
from gm_mcp import Permission, RequestContext, ToolRegistry, tool
from openai import AsyncOpenAI
from gm_auth.dependencies import identity_dependency
from gm_auth.models import AuthIdentity
from gm_auth.models import memberships, users

from app.auth import auth_service
from app.config import get_settings
from app.database import create_database_engine
from app.drive_storage import download_private_file, folder_status, save_private_file, save_quote_pdf
from app.models import Activity, CashMovement, Customer, CustomerPayment, FinancialAccount, FollowUp, HistoryCard, Installation, InstallationAssignment, InventoryItem, InventoryMovement, OfflineOperation, Project, ProjectExpense, ProfitabilityAdjustment, Purchase, PurchaseCorrection, PurchaseLine, PushSubscription, Quote, QuotePackage, Receivable, Sale, SaleCorrection, Supplier, SupplierPayment, WorkOrderMaterial
from app.reminders import send_due_followup_pushes
from app.roles import ROLE_LABELS, ROLE_PERMISSIONS, canonical_role
from app.web_push import send_push, validate_push_endpoint, vapid_public_key

settings = get_settings()
engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
router = APIRouter(prefix="/v1", tags=["arcoenergy"])
_agent_services: dict[str, AgentService] = {}
_agent_conversations: dict[tuple[str, str], Conversation] = {}


def require_permissions(service, *required: str):
    """Check current membership permissions so role changes apply immediately."""
    token_identity = identity_dependency(service)

    def dependency(identity: AuthIdentity = Depends(token_identity)):
        with service.engine.connect() as connection:
            row = connection.execute(
                select(users.c.email, users.c.name, memberships.c.roles, memberships.c.permissions)
                .join(memberships, memberships.c.user_id == users.c.id)
                .where(
                    users.c.id == identity.user_id,
                    users.c.is_active.is_(True),
                    memberships.c.organization_id == identity.organization_id,
                )
            ).mappings().first()
        if row is None:
            raise HTTPException(status_code=401, detail="Active organization membership required.")
        current = AuthIdentity(
            identity.user_id, identity.organization_id, frozenset(row["roles"] or []),
            frozenset(row["permissions"] or []), row["email"], row["name"],
        )
        if not set(required) <= current.permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current

    return dependency


def require_any_permission(service, *allowed: str):
    """Allow one of a small set of permissions, using the current membership."""
    token_identity = identity_dependency(service)

    def dependency(identity: AuthIdentity = Depends(token_identity)):
        with service.engine.connect() as connection:
            row = connection.execute(
                select(users.c.email, users.c.name, memberships.c.roles, memberships.c.permissions)
                .join(memberships, memberships.c.user_id == users.c.id)
                .where(
                    users.c.id == identity.user_id,
                    users.c.is_active.is_(True),
                    memberships.c.organization_id == identity.organization_id,
                )
            ).mappings().first()
        if row is None:
            raise HTTPException(status_code=401, detail="Active organization membership required.")
        current = AuthIdentity(
            identity.user_id, identity.organization_id, frozenset(row["roles"] or []),
            frozenset(row["permissions"] or []), row["email"], row["name"],
        )
        if not set(allowed).intersection(current.permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions.")
        return current

    return dependency


def _current_permissions(identity: AuthIdentity) -> frozenset[str]:
    """Read current grants for conditional record scoping, never stale token claims."""
    with auth_service.engine.connect() as connection:
        row = connection.execute(
            select(users.c.is_active, memberships.c.permissions)
            .join(memberships, memberships.c.user_id == users.c.id)
            .where(users.c.id == identity.user_id, memberships.c.organization_id == identity.organization_id)
        ).mappings().first()
    if row is None or not row["is_active"]:
        raise HTTPException(401, "Active organization membership required.")
    return frozenset(row["permissions"] or [])


def get_db():
    with SessionLocal() as session:
        yield session


def _serialize(row):
    if row is None:
        return None
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _serialize_inventory_item(row: InventoryItem, identity: AuthIdentity) -> dict:
    result = _serialize(row)
    result.pop("low_stock_alert_active", None)
    if "inventory:manage" not in identity.permissions:
        result.pop("restock_responsible_email", None)
    if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
        result.pop("unit_cost", None)
    return result


def _serialize_followup(row: FollowUp) -> dict:
    result = _serialize(row)
    result.pop("push_claimed_at", None)
    result.pop("push_notified_at", None)
    return result


class CustomerInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    phone: str = ""
    email: str = ""
    city: str = ""
    address: str = ""


class QuoteInput(BaseModel):
    customer_id: str
    panel_count: int = Field(ge=4, le=20)
    installation_address: str = ""
    installation_city: str = ""
    inverter: str = ""
    payment_method: str = "Contado"


class InverterOptionInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    price_mxn: Decimal = Field(ge=0)


class QuotePackageInput(BaseModel):
    panel_brand: str = Field(min_length=2, max_length=100)
    panel_watts: int = Field(ge=100, le=1000)
    panel_unit_price: Decimal = Field(ge=0)
    structure_name: str = Field(min_length=2, max_length=120)
    structure_price: Decimal = Field(ge=0)
    inverter_options: list[InverterOptionInput] = Field(min_length=1, max_length=6)
    default_inverter: str = Field(min_length=2, max_length=120)
    payment_methods: list[str] = Field(min_length=1, max_length=6)
    enabled: bool = True
    approved_prices: bool = False

    @field_validator("payment_methods")
    @classmethod
    def payment_methods_are_supported(cls, values: list[str]) -> list[str]:
        supported = {"Contado", "Financiamiento", "Plan 24"}
        cleaned = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not cleaned or not set(cleaned) <= supported:
            raise ValueError("Usa una o más formas de pago predefinidas.")
        return cleaned

    @field_validator("inverter_options")
    @classmethod
    def inverter_names_are_unique(cls, values: list[InverterOptionInput]) -> list[InverterOptionInput]:
        names = [value.name.strip().casefold() for value in values]
        if len(names) != len(set(names)):
            raise ValueError("No repitas el nombre de un inversor.")
        return values

    def validate_default_inverter(self) -> None:
        if self.default_inverter not in {item.name for item in self.inverter_options}:
            raise HTTPException(422, "El inversor predeterminado debe existir en las opciones del paquete.")


class FollowUpDoneInput(BaseModel):
    done: bool


class QuoteStatusInput(BaseModel):
    status: str


class PublicLeadInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    phone: str = Field(min_length=10, max_length=40)
    email: str = Field(default="", max_length=180)
    city: str = Field(min_length=2, max_length=120)
    address: str = Field(default="", max_length=500)
    privacy_consent: bool
    website: str = Field(default="", max_length=200)

    @field_validator("phone")
    @classmethod
    def phone_has_enough_digits(cls, value: str) -> str:
        if sum(character.isdigit() for character in value) < 10:
            raise ValueError("Captura un teléfono con al menos 10 dígitos.")
        return value.strip()


class AgentChatInput(BaseModel):
    prompt: str = Field(default="", max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=80)


def _agent_registry(audience: str) -> ToolRegistry:
    registry = ToolRegistry()
    if audience == "public":
        @tool(
            name="arcoenergy.public_system_sizes",
            description="Consulta los tamaños de sistema activos. Si hay precios aprobados, puede preparar una cotización estimada para el número de paneles solicitado y un inversor configurado. Nunca devuelve precios no aprobados.",
            input_schema={"type": "object", "properties": {"panel_count": {"type": "integer", "minimum": 4, "maximum": 20}, "inverter": {"type": "string", "maxLength": 120}}, "additionalProperties": False},
            permission=Permission.READ,
        )
        def public_system_sizes(*, context: RequestContext, panel_count: int | None = None, inverter: str = ""):
            with SessionLocal() as db:
                rows = db.scalars(select(QuotePackage).where(QuotePackage.enabled.is_(True)).order_by(QuotePackage.panel_count)).all()
                result = {
                    "available_panel_counts": [row.panel_count for row in rows],
                    "pricing_approved": bool(rows) and all(row.pricing_approved for row in rows),
                    "note": "No estimes ni inventes precios. Si el paquete elegido no está aprobado, pide los datos de contacto para que el equipo prepare la propuesta.",
                }
                if panel_count is None:
                    return result
                package = next((row for row in rows if row.panel_count == panel_count), None)
                if package is None:
                    return {**result, "quote": None, "note": "No hay un paquete activo para esa cantidad de paneles."}
                if not package.pricing_approved:
                    return {**result, "pricing_approved": False, "quote": None, "note": "El precio de este paquete aún no está aprobado. No proporciones una cantidad; ofrece que el equipo prepare la propuesta."}
                result["pricing_approved"] = True
                option = next((item for item in package.inverter_options if item.get("name") == inverter), None) if inverter else next((item for item in package.inverter_options if item.get("name") == package.default_inverter), None)
                if option is None:
                    return {**result, "quote": None, "available_inverters": [item.get("name") for item in package.inverter_options], "note": "El inversor solicitado no está configurado para este paquete."}
                total = Decimal(package.panel_unit_price) * panel_count + Decimal(package.structure_price) + Decimal(str(option["price_mxn"]))
                result["quote"] = {"panel_count": package.panel_count, "panel_brand": package.panel_brand, "panel_watts": package.panel_watts, "system_kw": round(package.panel_count * package.panel_watts / 1000, 2), "structure": package.structure_name, "inverter": option["name"], "total_mxn": str(total), "payment_methods": package.payment_methods, "note": "Estimación del catálogo aprobado, sujeta a evaluación técnica y propuesta formal del equipo."}
                return result

        registry.register(public_system_sizes)
    else:
        @tool(
            name="arcoenergy.crm_summary",
            description="Consulta conteos agregados de prospectos, cotizaciones y seguimientos abiertos; nunca devuelve datos personales.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            permission=Permission.READ,
            permissions={"customers:read"},
        )
        def crm_summary(*, context: RequestContext):
            with SessionLocal() as db:
                return {
                    "customers": db.scalar(select(func.count()).select_from(Customer)) or 0,
                    "quotes": db.scalar(select(func.count()).select_from(Quote)) or 0,
                    "open_followups": db.scalar(select(func.count()).select_from(FollowUp).where(FollowUp.done.is_(False))) or 0,
                }

        @tool(
            name="arcoenergy.crm_catalog",
            description="Consulta paquetes, opciones de inversor y el estado de aprobación de precios de Arco Energy.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            permission=Permission.READ,
            permissions={"quotes:read"},
        )
        def crm_catalog(*, context: RequestContext):
            with SessionLocal() as db:
                rows = db.scalars(select(QuotePackage).where(QuotePackage.enabled.is_(True)).order_by(QuotePackage.panel_count)).all()
                return [{"panel_count": row.panel_count, "panel_brand": row.panel_brand, "panel_watts": row.panel_watts,
                         "inverters": row.inverter_options, "default_inverter": row.default_inverter,
                         "pricing_approved": row.pricing_approved} for row in rows]

        registry.register(crm_summary)
        registry.register(crm_catalog)
    return registry


def _agent_service(audience: str) -> AgentService:
    if not settings.openai_api_key:
        raise HTTPException(503, "El asistente no está configurado en este entorno.")
    if audience not in _agent_services:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        _agent_services[audience] = AgentService(OpenAIProvider(client), _agent_registry(audience))
    return _agent_services[audience]


async def _run_agent_chat(data: AgentChatInput, audience: str, owner: str, identity: AuthIdentity | None = None):
    prompt = data.prompt.strip()
    if not prompt:
        raise HTTPException(422, "Escribe una pregunta para el asistente.")
    service = _agent_service(audience)
    conversation_id = data.conversation_id or str(uuid4())
    key = (owner, conversation_id)
    conversation = _agent_conversations.get(key)
    if conversation is None:
        conversation = Conversation(id=conversation_id)
        conversation.messages.append(Message("system", (
            "Eres el asistente de Arco Energy. Responde en español, con claridad y sin inventar datos, precios, ahorros, "
            "especificaciones ni compromisos. Si la persona pide cotizar, pregunta cuántos paneles desea y consulta la herramienta para la cantidad e inversor. Usa las herramientas disponibles para datos actuales. Si el catálogo dice "
            "que el precio aún no está aprobado, dilo con claridad y ofrece que el equipo configure el precio comercial. "
            "No tienes permiso para crear ni modificar registros; solo puedes consultar datos permitidos."
        )))
        _agent_conversations[key] = conversation
        if len(_agent_conversations) > 1000:
            _agent_conversations.pop(next(iter(_agent_conversations)))
    if identity:
        context = RequestContext(identity.user_id, identity.organization_id, "arcoenergy", frozenset({"read", *identity.permissions}), roles=identity.roles)
    else:
        context = RequestContext(f"public:{conversation_id}", settings.organization_id, "arcoenergy", frozenset({"read"}), roles=frozenset({"prospect"}))
    try:
        response = await service.respond(conversation=conversation, prompt=prompt, context=context, model="gpt-4o-mini")
    except Exception as exc:
        # Do not expose provider messages, request payloads, or credentials to the browser.
        raise HTTPException(502, "El asistente no pudo responder en este momento.") from exc
    return {"conversationId": conversation.id, "content": response.content}


class FollowUpInput(BaseModel):
    customer_id: str
    due_date: date
    note: str = ""
    quote_id: str | None = None
    assigned_to: str | None = None


class NoteInput(BaseModel):
    note: str = Field(min_length=1, max_length=5000)
    kind: str = "nota"


class InstallationInput(BaseModel):
    customer_id: str
    project_id: str | None = None
    quote_id: str | None = None
    scheduled_at: datetime | None = None
    lead_installer: str = ""
    assigned_installers: list[str] = Field(default_factory=list, max_length=10)
    notes: str = ""


class PushSubscriptionInput(BaseModel):
    endpoint: str = Field(min_length=16, max_length=4096)
    keys: dict[str, str]

    @field_validator("keys")
    @classmethod
    def validate_keys(cls, value: dict[str, str]) -> dict[str, str]:
        if set(value) != {"p256dh", "auth"} or not value.get("p256dh") or len(value["p256dh"]) > 200 or not value.get("auth") or len(value["auth"]) > 100:
            raise ValueError("La suscripción push no contiene claves válidas.")
        return value

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        return validate_push_endpoint(value)


class PushSubscriptionDeleteInput(BaseModel):
    endpoint: str = Field(min_length=16, max_length=4096)

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        return validate_push_endpoint(value)


class InstallationChecklistItemInput(BaseModel):
    task: str = Field(min_length=2, max_length=120)
    done: bool


class InstallationChecklistInput(BaseModel):
    checklist: list[InstallationChecklistItemInput] = Field(min_length=1, max_length=20)


class SaleMaterialInput(BaseModel):
    item_id: str
    quantity: Decimal = Field(gt=0)


class SaleInput(BaseModel):
    quote_id: str
    sale_type: Literal["cash", "credit"]
    account_id: str | None = None
    due_date: date | None = None
    installment_count: int = Field(default=1, ge=1, le=60)
    installment_frequency: Literal["weekly", "biweekly", "monthly"] = "monthly"
    scheduled_at: datetime | None = None
    lead_installer: str = Field(min_length=1, max_length=180)
    assigned_installers: list[str] = Field(default_factory=list, max_length=10)
    notes: str = Field(default="", max_length=5000)
    materials: list[SaleMaterialInput] = Field(min_length=1, max_length=100)


class StockInput(BaseModel):
    item_id: str
    quantity: float = Field(gt=0)
    reason: str = "consumo en instalación"
    installation_id: str | None = None
    operation_id: str | None = Field(default=None, min_length=8, max_length=80)


class StockIssueLineInput(BaseModel):
    work_order_material_id: str
    quantity: Decimal = Field(gt=0)


class StockIssueInput(BaseModel):
    installation_id: str
    document_reference: str = Field(default="", max_length=80)
    lines: list[StockIssueLineInput] = Field(min_length=1, max_length=100)

    @field_validator("lines")
    @classmethod
    def material_lines_are_unique(cls, values: list[StockIssueLineInput]) -> list[StockIssueLineInput]:
        ids = [line.work_order_material_id for line in values]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada material de la orden debe aparecer una sola vez.")
        return values


class InventoryReturnInput(BaseModel):
    out_movement_id: str
    quantity: float = Field(gt=0)
    condition: Literal["usable", "damaged"] = "usable"
    reason: str = Field(default="Devolución de material sobrante", max_length=180)
    operation_id: str | None = Field(default=None, min_length=8, max_length=80)


class StockReceiptInput(BaseModel):
    item_id: str
    quantity: float = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    reason: str = "entrada de almacén"


class InventoryItemInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = Field(default="", max_length=1000)
    category: str = Field(default="", max_length=100)
    subcategory: str = Field(default="", max_length=100)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=120)
    supplier_id: str | None = None
    barcode: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="pieza", max_length=40)
    minimum_quantity: float = Field(default=0, ge=0)
    restock_responsible_email: str = Field(default="", max_length=180)
    initial_quantity: float = Field(default=0, ge=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)


class InventoryItemUpdateInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = Field(default="", max_length=1000)
    category: str = Field(default="", max_length=100)
    subcategory: str = Field(default="", max_length=100)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=120)
    supplier_id: str | None = None
    barcode: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="pieza", max_length=40)
    minimum_quantity: float = Field(default=0, ge=0)
    restock_responsible_email: str = Field(default="", max_length=180)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("name", "unit")
    @classmethod
    def trim_required_catalog_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo es obligatorio.")
        return value


class PurchaseCatalogItemInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    category: str = Field(default="", max_length=100)
    subcategory: str = Field(default="", max_length=100)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=120)
    supplier_id: str | None = None
    barcode: str | None = Field(default=None, max_length=120)
    unit: str = Field(default="pieza", min_length=1, max_length=40)

    @field_validator("name", "unit")
    @classmethod
    def trim_required_catalog_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo es obligatorio.")
        return value


class ExpenseInput(BaseModel):
    installation_id: str | None = None
    project_id: str | None = None
    account_id: str | None = None
    category: str = "Viáticos"
    expense_type: Literal["fixed", "variable", "unclassified"] = "unclassified"
    description: str = Field(min_length=2, max_length=240)
    amount: Decimal = Field(gt=0)
    receipt_url: str = ""
    occurred_on: date = Field(default_factory=date.today)
    operation_id: str | None = Field(default=None, min_length=8, max_length=80)


class ProjectInput(BaseModel):
    customer_id: str
    name: str = Field(min_length=2, max_length=180)
    notes: str = Field(default="", max_length=5000)

    @field_validator("name")
    @classmethod
    def normalize_project_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Escribe un nombre para el proyecto.")
        return value


class ProjectUpdateInput(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    notes: str | None = Field(default=None, max_length=5000)


class FinancialAccountInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    account_type: Literal["cash", "bank"]
    opening_balance: Decimal = Field(ge=0)
    opening_balance_date: date


class CashMovementInput(BaseModel):
    account_id: str
    direction: Literal["in", "out"]
    amount: Decimal = Field(gt=0)
    category: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=2, max_length=2000)
    occurred_on: date = Field(default_factory=date.today)


class CashTransferInput(BaseModel):
    source_account_id: str
    destination_account_id: str
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    description: str = Field(min_length=2, max_length=2000)
    occurred_on: date = Field(default_factory=date.today)


class SupplierInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    rfc: str = Field(default="", max_length=20)
    phone: str = Field(default="", max_length=40)
    email: str = Field(default="", max_length=180)
    payment_terms: Literal["cash", "credit"] = "cash"
    credit_days: int = Field(default=0, ge=0, le=365)

    @field_validator("credit_days")
    @classmethod
    def credit_days_required_for_credit_terms(cls, value: int, info):
        if info.data.get("payment_terms") == "credit" and value < 1:
            raise ValueError("Indica los días de crédito acordados con el proveedor.")
        return value


class PurchaseLineInput(BaseModel):
    item_id: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(gt=0)


class PurchaseInput(BaseModel):
    supplier_id: str
    invoice_number: str = Field(default="", max_length=100)
    payment_terms: Literal["cash", "credit"]
    purchase_date: date = Field(default_factory=date.today)
    due_date: date | None = None
    lines: list[PurchaseLineInput] = Field(min_length=1, max_length=100)
    initial_payment: Decimal = Field(default=Decimal("0"), ge=0)
    payment_account_id: str | None = None
    payment_reference: str = Field(default="", max_length=180)

    @model_validator(mode="after")
    def purchase_items_are_unique(self):
        item_ids = [line.item_id for line in self.lines]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Cada artículo debe aparecer una sola vez en la compra.")
        return self


class PurchaseInvoiceXmlInput(BaseModel):
    xml: str = Field(min_length=1, max_length=2_097_152)


class SupplierPaymentInput(BaseModel):
    amount: Decimal = Field(gt=0)
    account_id: str
    paid_on: date = Field(default_factory=date.today)
    reference: str = Field(default="", max_length=180)


class PaymentCorrectionInput(BaseModel):
    reason: str = Field(min_length=5, max_length=120)

    @field_validator("reason")
    @classmethod
    def reason_must_contain_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 5:
            raise ValueError("Describe el motivo de la corrección (mínimo 5 caracteres).")
        return normalized


class ProfitabilityAdjustmentInput(BaseModel):
    installation_id: str | None = None
    adjustment_type: Literal["return", "bonification"]
    description: str = Field(min_length=3, max_length=240)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    occurred_on: date = Field(default_factory=date.today)

    @field_validator("description")
    @classmethod
    def adjustment_description_has_text(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("Describe la devolución o bonificación.")
        return normalized


class ReceivableInput(BaseModel):
    customer_id: str
    due_date: date
    amount: Decimal = Field(gt=0)
    installment_number: int = Field(default=1, ge=1)
    quote_id: str | None = None
    payment_method: str = "Transferencia"


class PaymentInput(BaseModel):
    amount: Decimal = Field(gt=0)
    account_id: str
    paid_on: date = Field(default_factory=date.today)
    reference: str = Field(default="", max_length=180)


class TeamMemberInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    email: str
    password: str = Field(min_length=12)
    role: str


class TeamRoleInput(BaseModel):
    role: str


class HistorySourceArtifactInput(BaseModel):
    artifact_type: str = Field(min_length=1, max_length=60)
    reference: str = Field(min_length=1, max_length=1000)
    channel: str = Field(default="", max_length=80)
    location: str = Field(default="", max_length=240)
    sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")

    @field_validator("artifact_type", "reference")
    @classmethod
    def required_artifact_fields_have_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Indica el tipo y la referencia durable de la fuente.")
        return value


class HistorySourceLinkInput(BaseModel):
    artifact_index: int = Field(ge=0, le=19)
    relation: Literal["literal", "transcription", "paraphrase", "inference", "validation", "reconstruction"]
    location: str = Field(default="", max_length=240)


class HistoryCardInput(BaseModel):
    story_id: str = Field(min_length=1, max_length=30)
    version: int = Field(ge=1)
    iteration: str = Field(min_length=1, max_length=80)
    stakeholder: str = Field(min_length=1, max_length=180)
    source_literal: str = Field(min_length=1)
    source_type: str = Field(min_length=1, max_length=40)
    source_reference: str = Field(min_length=1, max_length=1000)
    source_artifacts: list[HistorySourceArtifactInput] = Field(default_factory=list, max_length=20)
    source_links: list[HistorySourceLinkInput] = Field(default_factory=list, max_length=20)
    source_language: str = Field(default="es", min_length=2, max_length=20)
    source_attribution: str = Field(default="", max_length=180)
    source_occurred_at: str | None = Field(default=None, max_length=80)
    source_confidence: Literal["verbatim", "transcription", "paraphrase", "reconstruction", "needs_validation"] = "needs_validation"
    normalized_story: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    linked_cards: list[str] = Field(default_factory=list)

    @field_validator("source_literal")
    @classmethod
    def source_literal_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Conserva el relato literal o la transcripción fuente.")
        return value

    @field_validator("source_reference")
    @classmethod
    def source_reference_is_durable(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Registra una referencia durable al artefacto fuente.")
        return value


@router.get("/history-cards", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def list_history_cards(db: Session = Depends(get_db)):
    return [_serialize(row) for row in db.scalars(select(HistoryCard).order_by(HistoryCard.story_id, HistoryCard.version)).all()]


@router.post("/history-cards", status_code=201, dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def append_history_card(data: HistoryCardInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    latest = db.scalar(select(func.max(HistoryCard.version)).where(HistoryCard.story_id == data.story_id)) or 0
    if data.version != latest + 1:
        raise HTTPException(409, f"La siguiente versión disponible para {data.story_id} es {latest + 1}.")
    values = data.model_dump()
    artifacts = values.pop("source_artifacts")
    links = values["source_links"]
    if not artifacts:
        artifacts = [{
            "artifact_type": data.source_type,
            "reference": data.source_reference,
            "channel": data.source_type,
            "location": "",
            "sha256": None,
        }]
    if not links:
        relation = {
            "verbatim": "literal", "transcription": "transcription", "paraphrase": "paraphrase",
            "reconstruction": "reconstruction", "needs_validation": "reconstruction",
        }[data.source_confidence]
        links = [{"artifact_index": 0, "relation": relation, "location": ""}]
    if any(link["artifact_index"] >= len(artifacts) for link in links):
        raise HTTPException(422, "Cada relación de fuente debe apuntar a un artefacto registrado.")
    values["source_artifact"] = {"artifacts": artifacts}
    values["source_links"] = links
    values["source_attribution"] = data.source_attribution or data.stakeholder
    row = HistoryCard(**values, recorded_by=identity.email)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, f"La siguiente versión disponible para {data.story_id} es {latest + 1}.")
    db.refresh(row)
    return _serialize(row)


@router.get("/catalog", dependencies=[Depends(require_permissions(auth_service, "quotes:read"))])
def catalog(db: Session = Depends(get_db)):
    rows = db.scalars(select(QuotePackage).order_by(QuotePackage.panel_count)).all()
    packages = []
    for row in rows:
        selected = next((option for option in row.inverter_options if option.get("name") == row.default_inverter), None)
        inverter_price = Decimal(str(selected.get("price_mxn", 0))) if selected else Decimal("0")
        packages.append({
            **_serialize(row),
            "system_kw": round(row.panel_count * row.panel_watts / 1000, 2),
            "inverter": row.default_inverter,
            "price_mxn": Decimal(row.panel_unit_price) * row.panel_count + Decimal(row.structure_price) + inverter_price,
            "catalog_status": "approved" if row.pricing_approved else "pending_approval",
        })
    return {
        "packages": packages,
        "payment_methods": ["Contado", "Financiamiento", "Plan 24"],
        "catalog_note": "Configura los precios y condiciones comerciales vigentes antes de cotizar.",
    }


@router.put("/catalog/{panel_count}", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def update_catalog_package(panel_count: int, data: QuotePackageInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if not 4 <= panel_count <= 20:
        raise HTTPException(422, "El paquete debe tener de 4 a 20 paneles.")
    data.validate_default_inverter()
    row = db.scalar(select(QuotePackage).where(QuotePackage.panel_count == panel_count))
    if row is None:
        row = QuotePackage(panel_count=panel_count)
        db.add(row)
    row.panel_brand = data.panel_brand.strip()
    row.panel_watts = data.panel_watts
    row.panel_unit_price = data.panel_unit_price
    row.structure_name = data.structure_name.strip()
    row.structure_price = data.structure_price
    row.inverter_options = [item.model_dump(mode="json") for item in data.inverter_options]
    row.default_inverter = data.default_inverter.strip()
    row.payment_methods = data.payment_methods
    row.enabled = data.enabled
    row.pricing_approved = data.approved_prices
    row.updated_by = identity.email
    db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/customers", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def list_customers(db: Session = Depends(get_db)):
    return [_serialize(row) for row in db.scalars(select(Customer).order_by(Customer.created_at.desc())).all()]


@router.post("/public/leads", status_code=201)
def create_public_lead(data: PublicLeadInput, db: Session = Depends(get_db)):
    if data.website.strip():
        return {"accepted": True}
    if not data.privacy_consent:
        raise HTTPException(422, "Necesitamos tu consentimiento para contactarte sobre esta solicitud.")
    row = Customer(name=data.name.strip(), phone=data.phone, email=data.email.strip().lower(), city=data.city.strip(), address=data.address.strip(), source="public_web")
    db.add(row); db.flush()
    db.add(Activity(customer_id=row.id, kind="prospecto web", note="Solicitud recibida desde el sitio público."))
    db.commit(); db.refresh(row)
    return {"accepted": True, "reference": row.id}


@router.post("/public/agent/chat")
async def public_agent_chat(data: AgentChatInput):
    return await _run_agent_chat(data, "public", "public-session")


@router.post("/agent/chat", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
async def internal_agent_chat(data: AgentChatInput, identity: AuthIdentity = Depends(identity_dependency(auth_service))):
    return await _run_agent_chat(data, "internal", identity.user_id, identity)


@router.post("/customers", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def create_customer(data: CustomerInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = Customer(**data.model_dump(), source="crm")
    db.add(row); db.commit(); db.refresh(row)
    db.add(Activity(customer_id=row.id, kind="cliente creado", note="Registro inicial del cliente.", created_by=identity.email)); db.commit()
    return _serialize(row)


@router.get("/customers/{customer_id}/activity", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def customer_activity(customer_id: str, db: Session = Depends(get_db)):
    if not db.get(Customer, customer_id): raise HTTPException(404, "Cliente no encontrado.")
    rows = db.scalars(select(Activity).where(Activity.customer_id == customer_id).order_by(Activity.created_at.desc())).all()
    return [_serialize(row) for row in rows]


@router.get("/customers/{customer_id}", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    row = db.get(Customer, customer_id)
    if not row: raise HTTPException(404, "Cliente no encontrado.")
    return _serialize(row)


@router.post("/customers/{customer_id}/activity", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def add_customer_activity(customer_id: str, data: NoteInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if not db.get(Customer, customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = Activity(customer_id=customer_id, kind=data.kind, note=data.note, created_by=identity.email)
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.post("/quotes", status_code=201, dependencies=[Depends(require_permissions(auth_service, "quotes:write"))])
def create_quote(data: QuoteInput, db: Session = Depends(get_db)):
    customer = db.get(Customer, data.customer_id)
    if not customer: raise HTTPException(404, "Cliente no encontrado.")
    package = db.scalar(select(QuotePackage).where(QuotePackage.panel_count == data.panel_count, QuotePackage.enabled.is_(True)))
    if package is None:
        raise HTTPException(422, "No hay un paquete activo para esta cantidad de paneles.")
    if not package.pricing_approved:
        raise HTTPException(409, "El paquete requiere aprobación comercial antes de generar una cotización.")
    inverter = data.inverter or package.default_inverter
    inverter_option = next((item for item in package.inverter_options if item.get("name") == inverter), None)
    if inverter_option is None:
        raise HTTPException(422, "Selecciona un inversor configurado para este paquete.")
    if data.payment_method not in package.payment_methods:
        raise HTTPException(422, "Selecciona una forma de pago disponible para este paquete.")
    inverter_cost = Decimal(str(inverter_option["price_mxn"]))
    panel_subtotal = Decimal(package.panel_unit_price) * data.panel_count
    structure_cost = Decimal(package.structure_price)
    total = panel_subtotal + inverter_cost + structure_cost
    sequence = db.execute(text("SELECT nextval('ae_quote_folio_seq')")).scalar_one()
    folio = f"AE-{datetime.now(timezone.utc).year}-{sequence:05d}"
    row = Quote(
        folio=folio,
        customer_id=customer.id,
        installation_address=data.installation_address.strip() or customer.address,
        installation_city=data.installation_city.strip() or customer.city,
        panel_count=data.panel_count,
        panel_brand=package.panel_brand,
        panel_watts=package.panel_watts,
        structure_name=package.structure_name,
        inverter=inverter,
        payment_method=data.payment_method,
        panel_subtotal=panel_subtotal,
        structure_cost=structure_cost,
        inverter_cost=inverter_cost,
        total=total,
        status="draft",
        pricing_approved=package.pricing_approved,
    )
    db.add(row); db.flush()
    db.add(Activity(customer_id=customer.id, kind="cotización creada", note=f"Cotización {folio}, por ${total:,.2f} MXN.")); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/quotes", dependencies=[Depends(require_permissions(auth_service, "quotes:read"))])
def list_quotes(db: Session = Depends(get_db)):
    rows = db.scalars(select(Quote).order_by(Quote.created_at.desc())).all()
    return [{**_serialize(row), "customer": _serialize(db.get(Customer, row.customer_id))} for row in rows]


@router.patch("/quotes/{quote_id}/status", dependencies=[Depends(require_permissions(auth_service, "quotes:write"))])
def update_quote_status(quote_id: str, data: QuoteStatusInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if data.status not in {"draft", "sent", "accepted", "declined"}:
        raise HTTPException(422, "Estado de cotización no reconocido.")
    row = db.get(Quote, quote_id)
    if row is None: raise HTTPException(404, "Cotización no encontrada.")
    if not row.pricing_approved and data.status != "draft":
        raise HTTPException(409, "Aprueba el paquete comercial antes de avanzar esta cotización.")
    row.status = data.status
    db.add(Activity(customer_id=row.customer_id, kind="cotización actualizada", note=f"{row.folio}: {data.status}.", created_by=identity.email))
    db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/quotes/{quote_id}/pdf", dependencies=[Depends(require_permissions(auth_service, "quotes:read"))])
def quote_pdf(quote_id: str, db: Session = Depends(get_db)):
    row = db.get(Quote, quote_id)
    if not row: raise HTTPException(404, "Cotización no encontrada.")
    if not row.pricing_approved: raise HTTPException(409, "El paquete de esta cotización requiere aprobación antes de descargar el PDF.")
    customer = db.get(Customer, row.customer_id)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise HTTPException(503, "Generador PDF no está instalado.") from exc
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFillColorRGB(.09, .25, .19); pdf.rect(0, 640, 612, 152, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1); pdf.setFont("Helvetica-Bold", 23); pdf.drawString(48, 748, "arcoenergy")
    pdf.setFont("Helvetica", 10); pdf.drawString(48, 723, "PROPUESTA DE SISTEMA SOLAR")
    pdf.drawRightString(564, 748, row.folio)
    pdf.setFillColorRGB(.09, .17, .14); pdf.setFont("Helvetica-Bold", 16); pdf.drawString(48, 600, customer.name if customer else "Cliente")
    install_city = row.installation_city or (customer.city if customer else "Por definir")
    install_address = row.installation_address or (customer.address if customer else "")
    pdf.setFont("Helvetica", 10); pdf.drawString(48, 580, f"Instalación: {install_city}")
    if install_address:
        pdf.drawString(48, 562, f"Domicilio: {install_address[:85]}")
    pdf.drawString(48, 535, f"{row.panel_count} paneles {row.panel_brand} de {row.panel_watts} W")
    pdf.drawString(48, 515, f"Inversor: {row.inverter}")
    pdf.drawString(48, 495, f"Forma de pago: {row.payment_method}")
    pdf.line(48, 465, 564, 465)
    pdf.setFont("Helvetica", 11); pdf.drawString(48, 435, "Paneles"); pdf.drawRightString(564, 435, f"${float(row.panel_subtotal):,.2f} MXN")
    pdf.drawString(48, 412, row.structure_name); pdf.drawRightString(564, 412, f"${float(row.structure_cost):,.2f} MXN")
    pdf.drawString(48, 389, "Inversor"); pdf.drawRightString(564, 389, f"${float(row.inverter_cost):,.2f} MXN")
    pdf.setFont("Helvetica-Bold", 15); pdf.drawString(48, 345, "Inversión estimada")
    pdf.drawRightString(564, 345, f"${float(row.total):,.2f} MXN")
    pdf.setFont("Helvetica", 8); pdf.setFillColorRGB(.4, .45, .42)
    disclaimer = "Propuesta comercial sujeta a validación final de alcance y condiciones."
    pdf.drawString(48, 65, disclaimer)
    pdf.save(); buffer.seek(0)
    pdf_bytes = buffer.getvalue()
    drive_status = "pending-configuration"
    if settings.google_drive_service_account_json and settings.google_drive_folder_id:
        try:
            row.drive_file_id = save_quote_pdf(folio=row.folio, pdf=pdf_bytes, existing_file_id=row.drive_file_id)
            db.commit()
            drive_status = "saved"
        except Exception:
            db.rollback()
            drive_status = "upload-failed"
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{row.folio}.pdf"', "X-Drive-Status": drive_status})


@router.post("/followups", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def create_followup(data: FollowUpInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    assigned_to = (data.assigned_to or identity.email or "").strip().lower()
    if not assigned_to:
        raise HTTPException(422, "Selecciona a la persona responsable del seguimiento.")
    current_email = (identity.email or "").strip().lower()
    if assigned_to != current_email and "team:manage" not in _current_permissions(identity):
        raise HTTPException(403, "Solo administración puede asignar seguimientos a otra persona.")
    with auth_service.engine.connect() as connection:
        member = connection.execute(
            select(users.c.email, memberships.c.permissions)
            .join(memberships, memberships.c.user_id == users.c.id)
            .where(
                users.c.is_active.is_(True),
                func.lower(users.c.email) == assigned_to,
                memberships.c.organization_id == settings.organization_id,
            )
        ).mappings().first()
    if member is None or "customers:write" not in (member["permissions"] or []):
        raise HTTPException(422, "La persona responsable debe ser un usuario activo del equipo con permiso comercial.")
    values = data.model_dump(exclude={"assigned_to"})
    row = FollowUp(**values, assigned_to=assigned_to, created_by=identity.email or ""); db.add(row); db.flush()
    db.add(Activity(customer_id=row.customer_id, kind="seguimiento programado", note=f"{row.due_date}: {row.note}", created_by=identity.email)); db.commit(); db.refresh(row)
    return _serialize_followup(row)


@router.get("/followups", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def list_followups(identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    query = select(FollowUp).where(FollowUp.done.is_(False))
    if "team:manage" not in _current_permissions(identity):
        owner = (identity.email or "").strip().lower()
        if not owner:
            return []
        query = query.where(func.lower(FollowUp.assigned_to) == owner)
    rows = db.scalars(query.order_by(FollowUp.due_date)).all()
    return [{**_serialize_followup(row), "customer": _serialize(db.get(Customer, row.customer_id))} for row in rows]


@router.patch("/followups/{followup_id}", dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def update_followup(followup_id: str, data: FollowUpDoneInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = db.get(FollowUp, followup_id)
    if row is None: raise HTTPException(404, "Seguimiento no encontrado.")
    if "team:manage" not in _current_permissions(identity) and (row.assigned_to or "").strip().lower() != (identity.email or "").strip().lower():
        raise HTTPException(403, "Solo la persona responsable puede actualizar este seguimiento.")
    row.done = data.done
    if data.done:
        db.add(Activity(customer_id=row.customer_id, kind="seguimiento completado", note=f"Seguimiento del {row.due_date}: {row.note}", created_by=identity.email))
    db.commit(); db.refresh(row)
    return _serialize_followup(row)


def _validate_installer_emails(emails: list[str], primary_email: str = "") -> list[str]:
    normalized = sorted({email.strip().lower() for email in [*emails, primary_email] if email and email.strip()})
    if not normalized or len(normalized) > 10:
        raise HTTPException(422, "Selecciona de 1 a 10 instaladores para la cuadrilla.")
    with auth_service.engine.connect() as connection:
        active = set(connection.execute(
            select(func.lower(users.c.email))
            .join(memberships, memberships.c.user_id == users.c.id)
            .where(
                func.lower(users.c.email).in_(normalized),
                users.c.is_active.is_(True),
                memberships.c.organization_id == settings.organization_id,
                memberships.c.roles.contains(["instalador"]),
            )
        ).scalars().all())
    if active != set(normalized):
        raise HTTPException(422, "Cada integrante debe tener una cuenta activa con rol de instalador.")
    return normalized


def _record_installation_assignments(db: Session, installation_id: str, emails: list[str], assigned_by: str) -> None:
    db.add_all([
        InstallationAssignment(installation_id=installation_id, installer_email=email, assigned_by=assigned_by)
        for email in emails
    ])


def _installer_has_assignment(db: Session, installation: Installation, email: str) -> bool:
    normalized = (email or "").strip().lower()
    if not normalized:
        return False
    if installation.lead_installer.strip().lower() == normalized:
        return True
    return db.scalar(select(InstallationAssignment.id).where(
        InstallationAssignment.installation_id == installation.id,
        InstallationAssignment.installer_email == normalized,
    )) is not None


def _push_user_email(identity: AuthIdentity) -> str:
    email = (identity.email or "").strip().lower()
    allowed = "instalador" in identity.roles or "customers:read" in identity.permissions
    if not allowed or not email:
        raise HTTPException(403, "Las notificaciones push requieren acceso al CRM o rol instalador.")
    return email


def _validate_restock_responsible(email: str, db: Session) -> str:
    normalized = email.strip().lower()
    if not normalized:
        return ""
    active = db.execute(
        select(users.c.email)
        .join(memberships, memberships.c.user_id == users.c.id)
        .where(
            users.c.is_active.is_(True),
            memberships.c.organization_id == settings.organization_id,
            memberships.c.roles.contains(["instalador"]),
            func.lower(users.c.email) == normalized,
        )
    ).first()
    if active is None:
        raise HTTPException(422, "El responsable de reposición debe ser una cuenta activa de instalador.")
    return normalized


@router.get("/push/vapid-public-key")
def get_push_public_key(identity: AuthIdentity = Depends(require_any_permission(auth_service, "installations:read", "customers:read"))):
    _push_user_email(identity)
    secret = get_settings().web_push_vapid_secret
    if not secret:
        raise HTTPException(503, "Las notificaciones en segundo plano no están configuradas.")
    return {"public_key": vapid_public_key(secret)}


@router.get("/push/subscriptions/self")
def get_own_push_subscription(
    endpoint: str = Query(min_length=16, max_length=4096),
    identity: AuthIdentity = Depends(require_any_permission(auth_service, "installations:read", "customers:read")),
    db: Session = Depends(get_db),
):
    email = _push_user_email(identity)
    try:
        endpoint = validate_push_endpoint(endpoint)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    active = db.scalar(select(PushSubscription.id).where(
        PushSubscription.endpoint == endpoint,
        PushSubscription.user_email == email,
    )) is not None
    return {"active": active}


@router.post("/push/subscriptions", status_code=204)
def save_push_subscription(
    data: PushSubscriptionInput,
    identity: AuthIdentity = Depends(require_any_permission(auth_service, "installations:read", "customers:read")),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    email = _push_user_email(identity)
    if not get_settings().web_push_vapid_secret:
        raise HTTPException(503, "Las notificaciones en segundo plano no están configuradas.")
    row = db.scalar(select(PushSubscription).where(PushSubscription.endpoint == data.endpoint))
    if row is None:
        row = PushSubscription(endpoint=data.endpoint, user_email=email, p256dh=data.keys["p256dh"], auth=data.keys["auth"])
    else:
        row.user_email = email
        row.p256dh = data.keys["p256dh"]
        row.auth = data.keys["auth"]
    db.add(row)
    db.commit()
    if background_tasks is not None:
        low_items = db.scalars(select(InventoryItem).where(
            func.lower(InventoryItem.restock_responsible_email) == email,
            InventoryItem.minimum_quantity > 0,
        )).all()
        for item in low_items:
            _queue_low_stock_alert(db, background_tasks, item, force=True)
        if low_items:
            db.commit()
        background_tasks.add_task(send_due_followup_pushes, email)


@router.delete("/push/subscriptions", status_code=204)
def remove_push_subscription(
    data: PushSubscriptionDeleteInput,
    identity: AuthIdentity = Depends(require_any_permission(auth_service, "installations:read", "customers:read")),
    db: Session = Depends(get_db),
):
    email = _push_user_email(identity)
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == data.endpoint,
        PushSubscription.user_email == email,
    ).delete(synchronize_session=False)
    db.commit()


def _deliver_installation_push(subscriptions: list[dict[str, str]], folio: str) -> None:
    payload = {
        "title": "Nueva instalación asignada",
        "body": f"Orden {folio}. Abre la app para consultar los detalles.",
        "url": "/app/",
        "tag": f"arcoenergy-installation-{folio}",
    }
    _deliver_push_payload(subscriptions, payload)


def _deliver_push_payload(subscriptions: list[dict[str, str]], payload: dict[str, str]) -> bool:
    config = get_settings()
    if not config.web_push_vapid_secret:
        return False
    expired: list[str] = []
    delivered = False
    for subscription in subscriptions:
        status = send_push(subscription, payload, config.web_push_vapid_secret, config.web_push_subject)
        delivered = delivered or status in (201, 202)
        if status in (404, 410):
            expired.append(subscription["endpoint"])
    if expired:
        with SessionLocal() as db:
            db.query(PushSubscription).filter(PushSubscription.endpoint.in_(expired)).delete(synchronize_session=False)
            db.commit()
    return delivered


def _queue_installation_push(db: Session, background_tasks: BackgroundTasks | None, installers: list[str], folio: str) -> None:
    if background_tasks is None or not installers or not get_settings().web_push_vapid_secret:
        return
    rows = db.scalars(select(PushSubscription).where(PushSubscription.user_email.in_(installers))).all()
    subscriptions = [
        {"endpoint": row.endpoint, "p256dh": row.p256dh, "auth": row.auth}
        for row in rows
    ]
    if subscriptions:
        background_tasks.add_task(_deliver_installation_push, subscriptions, folio)


def _queue_low_stock_alert(db: Session, background_tasks: BackgroundTasks | None, item: InventoryItem, *, force: bool = False) -> None:
    reserved = db.scalar(
        select(func.coalesce(func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity), 0))
        .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
        .where(WorkOrderMaterial.item_id == item.id, Installation.status.notin_(("closed", "cancelled")))
    ) or 0
    available = max(Decimal(str(item.quantity)) - Decimal(str(reserved)), Decimal("0"))
    low = item.minimum_quantity > 0 and available <= Decimal(str(item.minimum_quantity))
    if not low:
        item.low_stock_alert_active = False
        return
    should_notify = force or not item.low_stock_alert_active
    item.low_stock_alert_active = True
    if not should_notify or not item.restock_responsible_email or background_tasks is None or not get_settings().web_push_vapid_secret:
        return
    rows = db.scalars(select(PushSubscription).where(
        func.lower(PushSubscription.user_email) == item.restock_responsible_email.lower(),
    )).all()
    subscriptions = [{"endpoint": row.endpoint, "p256dh": row.p256dh, "auth": row.auth} for row in rows]
    if subscriptions:
        payload = {
            "title": "Existencia baja",
            "body": f"{item.name}: quedan {available} {item.unit}; mínimo {item.minimum_quantity}.",
            "url": "/app/",
            "tag": f"arcoenergy-low-stock-{item.id}",
        }
        background_tasks.add_task(_deliver_push_payload, subscriptions, payload)


def _new_project_code() -> str:
    return f"AE-P-{datetime.now(timezone.utc).year}-{uuid4().hex[:8].upper()}"


def _project_result(project: Project, db: Session) -> dict:
    customer = db.get(Customer, project.customer_id)
    orders = db.scalars(select(Installation).where(Installation.project_id == project.id).order_by(Installation.folio)).all()
    return {
        **_serialize(project),
        "customer": {"id": customer.id, "name": customer.name, "city": customer.city} if customer else None,
        "work_orders": [{"id": order.id, "folio": order.folio, "status": order.status, "scheduled_at": order.scheduled_at} for order in orders],
        "status": "planning" if not orders else ("completed" if all(order.status in {"closed", "cancelled"} for order in orders) else "active"),
    }


@router.get("/projects")
def list_projects(identity: AuthIdentity = Depends(require_permissions(auth_service, "installations:read")), db: Session = Depends(get_db)):
    query = select(Project).order_by(Project.created_at.desc(), Project.code)
    if "instalador" in identity.roles:
        assigned_ids = select(InstallationAssignment.installation_id).where(
            InstallationAssignment.installer_email == (identity.email or "").strip().lower()
        )
        lead_ids = select(Installation.id).where(func.lower(Installation.lead_installer) == (identity.email or "").strip().lower())
        query = query.where(Project.id.in_(select(Installation.project_id).where(
            Installation.project_id.is_not(None), Installation.status != "cancelled",
            or_(Installation.id.in_(assigned_ids), Installation.id.in_(lead_ids)),
        )))
    return [_project_result(project, db) for project in db.scalars(query).all()]


@router.post("/projects", status_code=201, dependencies=[Depends(require_permissions(auth_service, "installations:write"))])
def create_project(data: ProjectInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if db.get(Customer, data.customer_id) is None:
        raise HTTPException(404, "Cliente no encontrado.")
    project = Project(code=_new_project_code(), customer_id=data.customer_id, name=data.name, notes=data.notes.strip(), created_by=identity.email or "")
    db.add(project); db.commit(); db.refresh(project)
    return _project_result(project, db)


@router.patch("/projects/{project_id}", dependencies=[Depends(require_permissions(auth_service, "installations:write"))])
def update_project(project_id: str, data: ProjectUpdateInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado.")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(422, "Incluye el nombre o las notas que quieres corregir.")
    if "name" in updates:
        project.name = updates["name"].strip()
        if len(project.name) < 2:
            raise HTTPException(422, "Escribe un nombre para el proyecto.")
    if "notes" in updates:
        project.notes = (updates["notes"] or "").strip()
    db.commit(); db.refresh(project)
    return _project_result(project, db)


@router.post("/installations", status_code=201, dependencies=[Depends(require_permissions(auth_service, "installations:write"))])
def create_installation(data: InstallationInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    customer = db.get(Customer, data.customer_id)
    if not customer: raise HTTPException(404, "Cliente no encontrado.")
    project = db.get(Project, data.project_id) if data.project_id else None
    if data.project_id and project is None: raise HTTPException(404, "Proyecto no encontrado.")
    if project and project.customer_id != customer.id: raise HTTPException(422, "El proyecto pertenece a otro cliente.")
    if project is None:
        project = Project(code=_new_project_code(), customer_id=customer.id, name=customer.name, created_by=identity.email or "")
        db.add(project); db.flush()
    installers = _validate_installer_emails(data.assigned_installers, data.lead_installer)
    primary = (data.lead_installer.strip().lower() or installers[0])
    row = Installation(customer_id=data.customer_id, project_id=project.id, quote_id=data.quote_id, scheduled_at=data.scheduled_at, lead_installer=primary, notes=data.notes, checklist=[{"task":"Confirmar materiales","done":False},{"task":"Asignar cuadrilla","done":True},{"task":"Visita de instalación","done":False},{"task":"Registrar consumos","done":False},{"task":"Cerrar proyecto","done":False}])
    db.add(row); db.flush()
    _record_installation_assignments(db, row.id, installers, identity.email or "")
    db.commit(); db.refresh(row)
    _queue_installation_push(db, background_tasks, installers, row.folio or row.id)
    return {**_serialize(row), "assigned_installers": installers, "confirmed_installers": []}


def _sale_result(db: Session, sale: Sale):
    quote = db.get(Quote, sale.quote_id)
    customer = db.get(Customer, sale.customer_id)
    installation = db.get(Installation, sale.installation_id)
    receivables = db.scalars(select(Receivable).where(Receivable.quote_id == sale.quote_id).order_by(Receivable.installment_number)).all()
    materials = db.scalars(select(WorkOrderMaterial).where(WorkOrderMaterial.installation_id == sale.installation_id)).all()
    assignments = db.scalars(select(InstallationAssignment).where(InstallationAssignment.installation_id == sale.installation_id)).all()
    correction = db.scalar(select(SaleCorrection).where(SaleCorrection.sale_id == sale.id))
    has_unreversed_collection = False
    if sale.sale_type == "credit" and receivables:
        credit_payments = db.scalars(select(CustomerPayment).join(Receivable, Receivable.id == CustomerPayment.receivable_id)
                                     .where(Receivable.quote_id == sale.quote_id)).all()
        reversed_payment_ids = {payment.reversal_of_id for payment in credit_payments if payment.reversal_of_id}
        has_unreversed_collection = any(payment.reversal_of_id is None and payment.id not in reversed_payment_ids for payment in credit_payments)
    credit_balance_clear = bool(receivables) and all(Decimal(row.paid_amount) == 0 for row in receivables) and not has_unreversed_collection
    progressed_tasks = any(task.get("done") and task.get("task") not in {"Confirmar materiales", "Asignar cuadrilla"} for task in (installation.checklist or [])) if installation else True
    has_stock_activity = db.scalar(select(InventoryMovement.id).where(InventoryMovement.installation_id == sale.installation_id).limit(1)) is not None
    can_reverse = bool(
        correction is None and sale.sale_type in {"cash", "credit"} and installation and installation.status == "assigned"
        and (sale.sale_type == "cash" or credit_balance_clear)
        and not progressed_tasks and not has_stock_activity
        and not any(row.confirmed_at for row in assignments)
        and all(Decimal(line.preissued_quantity) == 0 and Decimal(line.consumed_quantity) == 0 for line in materials)
    )
    item_names = {item.id: item.name for item in db.scalars(select(InventoryItem).where(InventoryItem.id.in_([line.item_id for line in materials]))).all()} if materials else {}
    return {
        **_serialize(sale),
        "quote": {"id": quote.id, "folio": quote.folio, "payment_method": quote.payment_method} if quote else None,
        "customer": {"id": customer.id, "name": customer.name, "phone": customer.phone, "email": customer.email, "city": customer.city} if customer else None,
        "installation": {**_serialize(installation), "project": _project_result(db.get(Project, installation.project_id), db) if installation and installation.project_id else None, "assigned_installers": [row.installer_email for row in assignments] or ([installation.lead_installer] if installation and installation.lead_installer else []), "confirmed_installers": [row.installer_email for row in assignments if row.confirmed_at]},
        "receivable": _serialize(receivables[0]) if receivables else None,
        "receivables": [_serialize(row) for row in receivables],
        "installment_count": len(receivables),
        "correction": _serialize(correction),
        "can_reverse": can_reverse,
        "materials": [{**_serialize(line), "item_name": item_names.get(line.item_id, "Artículo"), "quantity": line.requested_quantity, "remaining_quantity": max(Decimal(line.requested_quantity) - Decimal(line.consumed_quantity), Decimal("0"))} for line in materials],
    }


def _installment_due_date(first_due_date: date, installment_index: int, frequency: str) -> date:
    if frequency == "weekly":
        return first_due_date + timedelta(days=7 * installment_index)
    if frequency == "biweekly":
        return first_due_date + timedelta(days=14 * installment_index)
    month_index = first_due_date.year * 12 + first_due_date.month - 1 + installment_index
    year, month_zero_based = divmod(month_index, 12)
    month = month_zero_based + 1
    day = min(first_due_date.day, monthrange(year, month)[1])
    return date(year, month, day)


@router.get("/sales", dependencies=[Depends(require_permissions(auth_service, "sales:read"))])
def list_sales(db: Session = Depends(get_db)):
    rows = db.scalars(select(Sale).order_by(Sale.created_at.desc())).all()
    return [_sale_result(db, row) for row in rows]


@router.post("/sales/{sale_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "sales:write"))])
def reverse_sale(sale_id: str, data: PaymentCorrectionInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    if not ({"administrador", "admin", "contador"} & set(identity.roles)):
        raise HTTPException(403, "Solo administración o contabilidad puede corregir una venta.")
    sale = db.scalar(select(Sale).where(Sale.id == sale_id).with_for_update())
    if sale is None:
        raise HTTPException(404, "Venta no encontrada.")
    if sale.sale_type not in {"cash", "credit"}:
        raise HTTPException(409, "El tipo de venta no permite este flujo de corrección.")
    if db.scalar(select(SaleCorrection.id).where(SaleCorrection.sale_id == sale.id)):
        raise HTTPException(409, "Esta venta ya tiene una corrección registrada.")
    installation = db.scalar(select(Installation).where(Installation.id == sale.installation_id).with_for_update())
    if installation is None:
        raise HTTPException(409, "La venta no conserva su orden de trabajo relacionada.")
    assignments = db.scalars(select(InstallationAssignment).where(InstallationAssignment.installation_id == installation.id).with_for_update()).all()
    materials = db.scalars(select(WorkOrderMaterial).where(WorkOrderMaterial.installation_id == installation.id).with_for_update()).all()
    progressed_tasks = any(task.get("done") and task.get("task") not in {"Confirmar materiales", "Asignar cuadrilla"} for task in (installation.checklist or []))
    has_stock_activity = db.scalar(select(InventoryMovement.id).where(InventoryMovement.installation_id == installation.id).limit(1)) is not None
    if installation.status != "assigned" or progressed_tasks or has_stock_activity or any(row.confirmed_at for row in assignments) or any(
        Decimal(line.preissued_quantity) != 0 or Decimal(line.consumed_quantity) != 0 for line in materials
    ):
        raise HTTPException(409, "No se puede revertir: la orden ya inició o tiene materiales emitidos, consumidos o confirmados.")

    receivables = db.scalars(select(Receivable).where(Receivable.quote_id == sale.quote_id).with_for_update()).all()
    credit_payments = db.scalars(select(CustomerPayment).join(Receivable, Receivable.id == CustomerPayment.receivable_id)
                                 .where(Receivable.quote_id == sale.quote_id).with_for_update()).all()
    reversed_payment_ids = {payment.reversal_of_id for payment in credit_payments if payment.reversal_of_id}
    has_unreversed_collection = any(payment.reversal_of_id is None and payment.id not in reversed_payment_ids for payment in credit_payments)
    if sale.sale_type == "credit" and not receivables:
        raise HTTPException(409, "La venta a crédito no conserva sus cuotas enlazadas; revisa la cartera antes de corregirla.")
    if sale.sale_type == "credit" and (any(Decimal(row.paid_amount) != 0 for row in receivables) or has_unreversed_collection):
        raise HTTPException(409, "Revierte primero los cobros netos de la venta desde la bitácora de cada cuota.")

    cash_rows = db.scalars(select(CashMovement).where(
        CashMovement.source_type == "sale", CashMovement.source_id == sale.id,
    ).with_for_update()).all()
    reversal = None
    if sale.sale_type == "cash":
        if len(cash_rows) != 1:
            raise HTTPException(409, "La venta no conserva exactamente un ingreso de caja/banco enlazado; revisa el historial.")
        cash = cash_rows[0]
        if cash.reversal_of_id is not None or db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == cash.id)):
            raise HTTPException(409, "El ingreso de esta venta ya tiene una corrección registrada.")
        reversal = CashMovement(
            account_id=cash.account_id, direction="out", amount=cash.amount,
            category="Corrección de venta", description=f"Corrección de venta {sale.folio}: {data.reason}",
            occurred_on=date.today(), source_type="sale_reversal", source_id=sale.id,
            reversal_of_id=cash.id, created_by=identity.email or "",
        )
        db.add(reversal); db.flush()
    elif cash_rows:
        raise HTTPException(409, "La venta a crédito tiene un movimiento de contado inesperado; revisa la cuenta antes de corregirla.")
    db.add(SaleCorrection(
        sale_id=sale.id, cash_movement_id=reversal.id if reversal else None, amount=sale.total,
        reason=data.reason, created_by=identity.email or "",
    ))
    installation.status = "cancelled"
    for material in materials:
        item = db.get(InventoryItem, material.item_id)
        if item is not None:
            _queue_low_stock_alert(db, background_tasks, item)
    db.add(Activity(
        customer_id=sale.customer_id, kind="corrección de venta",
        note=f"{sale.folio} · orden {installation.folio or installation.id} cancelada: {data.reason}",
        created_by=identity.email or "",
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Esta venta ya tiene una corrección registrada.")
    db.refresh(sale)
    return _sale_result(db, sale)


@router.post("/sales", status_code=201, dependencies=[Depends(require_permissions(auth_service, "sales:write"))])
def create_sale(data: SaleInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    quote = db.scalar(select(Quote).where(Quote.id == data.quote_id).with_for_update())
    if quote is None: raise HTTPException(404, "Cotización no encontrada.")
    if quote.status != "accepted": raise HTTPException(422, "Registra primero que el cliente aceptó la cotización.")
    if not quote.pricing_approved: raise HTTPException(422, "La propuesta requiere aprobación comercial antes de registrarse como venta.")
    if db.scalar(select(Sale.id).where(Sale.quote_id == quote.id)):
        raise HTTPException(409, "Esta cotización ya fue registrada como venta.")
    customer = db.get(Customer, quote.customer_id)
    if customer is None: raise HTTPException(409, "El cliente de la cotización ya no está disponible.")

    installer_emails = _validate_installer_emails(data.assigned_installers, data.lead_installer)
    installer_email = data.lead_installer.strip().lower()

    account = None
    if data.sale_type == "cash":
        if not data.account_id or data.due_date:
            raise HTTPException(422, "Una venta de contado requiere una cuenta receptora y no lleva vencimiento de crédito.")
        if data.installment_count != 1:
            raise HTTPException(422, "Una venta de contado no puede incluir un plan de cuotas.")
        account = db.scalar(select(FinancialAccount).where(
            FinancialAccount.id == data.account_id,
            FinancialAccount.active.is_(True),
        ).with_for_update())
        if account is None: raise HTTPException(404, "Selecciona una cuenta de caja o banco activa.")
    else:
        if data.account_id or not data.due_date:
            raise HTTPException(422, "Una venta a crédito requiere fecha de vencimiento y no debe seleccionar cuenta de cobro todavía.")
        total_due = Decimal(quote.total).quantize(Decimal("0.01"))
        if total_due < Decimal(data.installment_count) * Decimal("0.01"):
            raise HTTPException(422, "El total no alcanza para generar el número de cuotas solicitado.")
        if db.scalar(select(Receivable.id).where(Receivable.quote_id == quote.id)):
            raise HTTPException(409, "Esta cotización ya tiene cuentas por cobrar registradas.")

    material_totals: dict[str, Decimal] = {}
    for line in data.materials:
        material_totals[line.item_id] = material_totals.get(line.item_id, Decimal("0")) + line.quantity
    locked_items = []
    for item_id, quantity in material_totals.items():
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == item_id).with_for_update())
        if item is None: raise HTTPException(404, "Uno de los materiales de la orden ya no existe en el almacén.")
        reserved = db.scalar(select(func.coalesce(func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity), 0))
            .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
            .where(WorkOrderMaterial.item_id == item_id, Installation.status.notin_(("closed", "cancelled")))) or 0
        available = Decimal(str(item.quantity)) - Decimal(str(reserved))
        if available < quantity:
            raise HTTPException(409, f"Existencia disponible insuficiente de {item.name}: disponibles {available}, requeridos {quantity}.")
        locked_items.append((item, quantity))

    if db.get_bind().dialect.name == "postgresql":
        sale_number = db.execute(text("SELECT nextval('ae_sale_folio_seq')")).scalar_one()
        work_number = db.execute(text("SELECT nextval('ae_work_order_folio_seq')")).scalar_one()
    else:
        sale_number = (db.scalar(select(func.count()).select_from(Sale)) or 0) + 1
        work_number = (db.scalar(select(func.count()).select_from(Installation).where(Installation.folio.is_not(None))) or 0) + 1
    year = datetime.now(timezone.utc).year
    sale_folio = f"AE-V-{year}-{sale_number:05d}"
    work_folio = f"AE-OT-{year}-{work_number:05d}"
    project = Project(code=_new_project_code(), customer_id=customer.id, name=customer.name, created_by=identity.email or "")
    db.add(project); db.flush()
    installation = Installation(
        folio=work_folio,
        customer_id=customer.id,
        project_id=project.id,
        quote_id=quote.id,
        scheduled_at=data.scheduled_at,
        lead_installer=installer_email,
        status="assigned",
        notes=data.notes.strip(),
        checklist=[{"task":"Confirmar materiales","done":True},{"task":"Asignar cuadrilla","done":True},{"task":"Visita de instalación","done":False},{"task":"Registrar consumos","done":False},{"task":"Cerrar proyecto","done":False}],
    )
    db.add(installation); db.flush()
    _record_installation_assignments(db, installation.id, installer_emails, identity.email or "")
    sale = Sale(folio=sale_folio, customer_id=customer.id, quote_id=quote.id, installation_id=installation.id,
        sale_type=data.sale_type, total=quote.total, created_by=identity.email or "")
    db.add(sale); db.flush()
    for item, quantity in locked_items:
        db.add(WorkOrderMaterial(
            installation_id=installation.id,
            item_id=item.id,
            requested_quantity=quantity,
            preissued_quantity=Decimal("0"),
            consumed_quantity=Decimal("0"),
            unit_cost=item.unit_cost,
            created_by=identity.email or "",
        ))
    db.flush()
    for item, _quantity in locked_items:
        _queue_low_stock_alert(db, background_tasks, item)
    if data.sale_type == "cash" and account is not None:
        db.add(CashMovement(account_id=account.id, direction="in", amount=quote.total,
            category="Venta de contado", description=f"{customer.name} · {sale_folio}",
            occurred_on=date.today(), source_type="sale", source_id=sale.id, created_by=identity.email or ""))
    elif data.due_date is not None:
        total_due = Decimal(quote.total).quantize(Decimal("0.01"))
        regular_amount = (total_due / data.installment_count).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        for installment_number in range(1, data.installment_count + 1):
            amount = regular_amount if installment_number < data.installment_count else total_due - regular_amount * (data.installment_count - 1)
            due_date = _installment_due_date(data.due_date, installment_number - 1, data.installment_frequency)
            db.add(Receivable(
                customer_id=customer.id, quote_id=quote.id, installment_number=installment_number,
                due_date=due_date, amount=amount, paid_amount=Decimal("0"),
                status="overdue" if due_date < date.today() else "pending",
                payment_method=quote.payment_method,
            ))
    db.commit(); db.refresh(sale)
    _queue_installation_push(db, background_tasks, installer_emails, work_folio)
    return _sale_result(db, sale)


# Keep the previous callable name for internal integrations while the route
# remains the single source-linked correction endpoint for both sale types.
reverse_cash_sale = reverse_sale


@router.get("/installations")
def list_installations(identity: AuthIdentity = Depends(require_permissions(auth_service, "installations:read")), db: Session = Depends(get_db)):
    query = select(Installation).order_by(Installation.scheduled_at)
    if "instalador" in identity.roles:
        assigned_ids = select(InstallationAssignment.installation_id).where(
            InstallationAssignment.installer_email == (identity.email or "").strip().lower()
        )
        query = query.where(Installation.status != "cancelled").where(or_(func.lower(Installation.lead_installer) == (identity.email or "").strip().lower(), Installation.id.in_(assigned_ids)))
    rows = db.scalars(query).all()
    reserved_by_item = {
        item_id: Decimal(quantity or 0)
        for item_id, quantity in db.execute(
            select(WorkOrderMaterial.item_id, func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity))
            .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
            .where(Installation.status.notin_(("closed", "cancelled")))
            .group_by(WorkOrderMaterial.item_id)
        ).all()
    }
    visible_materials = db.scalars(select(WorkOrderMaterial).where(
        WorkOrderMaterial.installation_id.in_([row.id for row in rows]),
    )).all() if rows else []
    materials_by_installation: dict[str, list[WorkOrderMaterial]] = {}
    for material in visible_materials:
        materials_by_installation.setdefault(material.installation_id, []).append(material)
    item_ids = {material.item_id for material in visible_materials}
    inventory_by_id = {item.id: item for item in db.scalars(
        select(InventoryItem).where(InventoryItem.id.in_(item_ids)),
    ).all()} if item_ids else {}
    result = []
    for row in rows:
        customer = db.get(Customer, row.customer_id)
        materials = materials_by_installation.get(row.id, [])
        assignments = db.scalars(select(InstallationAssignment).where(InstallationAssignment.installation_id == row.id)).all()
        serialized_materials = []
        for material in materials:
            item = inventory_by_id.get(material.item_id)
            remaining_to_issue = max(Decimal(material.requested_quantity) - Decimal(material.preissued_quantity), Decimal("0"))
            active = row.status not in {"closed", "cancelled"}
            other_reserved = max(reserved_by_item.get(material.item_id, Decimal("0")) - (remaining_to_issue if active else Decimal("0")), Decimal("0"))
            available_for_order = max(Decimal(str(item.quantity)) - other_reserved, Decimal("0")) if item and active else None
            shortage = max(remaining_to_issue - available_for_order, Decimal("0")) if available_for_order is not None else Decimal("0")
            serialized_materials.append({
                **_serialize(material),
                "item_name": item.name if item else "Artículo",
                "remaining_quantity": max(Decimal(material.requested_quantity) - Decimal(material.consumed_quantity), Decimal("0")),
                "remaining_to_issue": remaining_to_issue,
                "available_for_order": available_for_order,
                "shortage_quantity": shortage,
            })
        project = db.get(Project, row.project_id) if row.project_id else None
        result.append({**_serialize(row),
            "assigned_installers": [assignment.installer_email for assignment in assignments] or ([row.lead_installer] if row.lead_installer else []),
            "confirmed_installers": [assignment.installer_email for assignment in assignments if assignment.confirmed_at],
            # Installation readers need field contact details, not the full CRM
            # customer record (status/source and other private metadata).
            "customer": ({"id": customer.id, "name": customer.name, "city": customer.city,
                          "address": customer.address, "phone": customer.phone, "email": customer.email}
                         if customer else None),
            "project": {"id": project.id, "code": project.code, "name": project.name} if project else None,
            "materials": serialized_materials})
    return result


_MATERIAL_REQUEST_TYPES = {
    "application/pdf": (".pdf", b"%PDF-"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}
_MAX_MATERIAL_REQUEST_BYTES = 12 * 1024 * 1024
_EXPENSE_RECEIPT_TYPES = {
    "application/pdf": (".pdf", b"%PDF-"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}


@router.put("/installations/{installation_id}/material-request-file")
async def upload_material_request_file(
    installation_id: str,
    request: Request,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:issue")),
    db: Session = Depends(get_db),
):
    installation = db.get(Installation, installation_id)
    if installation is None:
        raise HTTPException(404, "Orden de trabajo no encontrada.")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    file_type = _MATERIAL_REQUEST_TYPES.get(content_type)
    if file_type is None:
        raise HTTPException(415, "Usa PDF, JPG, PNG o WebP.")
    try:
        declared_length = int(request.headers.get("content-length", "0"))
    except ValueError:
        raise HTTPException(400, "Tamaño de archivo no válido.") from None
    if declared_length > _MAX_MATERIAL_REQUEST_BYTES:
        raise HTTPException(413, "El archivo debe pesar 12 MB o menos.")
    collected = bytearray()
    async for chunk in request.stream():
        if len(collected) + len(chunk) > _MAX_MATERIAL_REQUEST_BYTES:
            raise HTTPException(413, "El archivo debe pesar 12 MB o menos.")
        collected.extend(chunk)
    content = bytes(collected)
    if not content:
        raise HTTPException(400, "El archivo está vacío.")
    if not content.startswith(file_type[1]) or (content_type == "image/webp" and content[8:12] != b"WEBP"):
        raise HTTPException(415, "El contenido del archivo no coincide con su formato.")
    raw_name = unquote(request.headers.get("x-document-name", "solicitud"))
    raw_name = raw_name.replace("\\", "/").split("/")[-1]
    filename = re.sub(r"[^\w.() -]", "_", raw_name, flags=re.UNICODE).strip(" .")[:220]
    expected_extension = file_type[0]
    if not filename.lower().endswith(expected_extension):
        filename = f"{filename.rsplit('.', 1)[0] if '.' in filename else filename}{expected_extension}"
    try:
        drive_id = save_private_file(
            filename=f"orden-{installation.folio or installation.id}-{filename}",
            content=content,
            content_type=content_type,
            existing_file_id=installation.material_request_drive_file_id,
        )
    except RuntimeError as error:
        if str(error) == "not_configured":
            raise HTTPException(503, "drive_not_configured") from None
        raise HTTPException(502, "No se pudo archivar el documento en Drive.") from None
    except Exception:
        raise HTTPException(502, "No se pudo archivar el documento en Drive.") from None
    installation.material_request_drive_file_id = drive_id
    installation.material_request_filename = filename
    installation.material_request_content_type = content_type
    installation.material_request_updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "saved": True,
        "filename": filename,
        "content_type": content_type,
        "updated_at": installation.material_request_updated_at.isoformat(),
    }


@router.get("/installations/{installation_id}/material-request-file")
def get_material_request_file(
    installation_id: str,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:issue")),
    db: Session = Depends(get_db),
):
    installation = db.get(Installation, installation_id)
    if installation is None:
        raise HTTPException(404, "Orden de trabajo no encontrada.")
    if not installation.material_request_drive_file_id:
        raise HTTPException(404, "Esta orden no tiene una solicitud archivada.")
    try:
        stored = download_private_file(installation.material_request_drive_file_id)
    except Exception:
        raise HTTPException(502, "No se pudo recuperar el documento archivado.") from None
    filename = installation.material_request_filename or "solicitud-materiales"
    return Response(
        content=stored.content,
        media_type=installation.material_request_content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{urlquote(filename)}"},
    )


@router.post("/installations/{installation_id}/confirm")
def confirm_installation_assignment(
    installation_id: str,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "installations:read")),
    db: Session = Depends(get_db),
):
    if "instalador" not in identity.roles or not identity.email:
        raise HTTPException(403, "Solo un instalador asignado puede confirmar la orden.")
    installation = db.scalar(select(Installation).where(Installation.id == installation_id).with_for_update())
    if installation is None:
        raise HTTPException(404, "Orden de trabajo no encontrada.")
    if installation.status == "cancelled":
        raise HTTPException(409, "La orden fue cancelada y ya no acepta confirmaciones.")
    email = identity.email.strip().lower()
    assignment = db.scalar(select(InstallationAssignment).where(
        InstallationAssignment.installation_id == installation_id,
        InstallationAssignment.installer_email == email,
    ).with_for_update())
    if assignment is None and installation.lead_installer.strip().lower() == email:
        assignment = InstallationAssignment(installation_id=installation.id, installer_email=email, assigned_by="")
        db.add(assignment); db.flush()
    if assignment is None:
        raise HTTPException(403, "Esta orden no está asignada a tu cuenta.")
    if assignment.confirmed_at is None:
        assignment.confirmed_at = datetime.now(timezone.utc)
        db.add(Activity(customer_id=installation.customer_id, kind="orden confirmada por instalador", note=f"{installation.folio or 'Orden'} · {email}", created_by=email))
        db.commit()
    return {"installation_id": installation.id, "installer_email": email, "confirmed_at": assignment.confirmed_at}


def _offline_operation_owner(identity: AuthIdentity) -> str:
    return (identity.email or identity.user_id).strip().casefold()


def _find_offline_operation(data: BaseModel, operation_type: str, identity: AuthIdentity, db: Session) -> OfflineOperation | None:
    operation_id = getattr(data, "operation_id", None)
    if not operation_id:
        return None
    owner = _offline_operation_owner(identity)
    payload = data.model_dump(mode="json", exclude={"operation_id"})
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    existing = db.scalar(select(OfflineOperation).where(
        OfflineOperation.owner_email == owner,
        OfflineOperation.operation_id == operation_id,
    ))
    if existing and (existing.operation_type != operation_type or existing.payload_hash != payload_hash):
        raise HTTPException(409, "El identificador de operación ya se usó con otros datos.")
    return existing


def _record_offline_operation(data: BaseModel, operation_type: str, result_id: str, identity: AuthIdentity, db: Session) -> None:
    operation_id = getattr(data, "operation_id", None)
    if not operation_id:
        return
    payload = data.model_dump(mode="json", exclude={"operation_id"})
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    db.add(OfflineOperation(
        owner_email=_offline_operation_owner(identity),
        operation_id=operation_id,
        operation_type=operation_type,
        payload_hash=payload_hash,
        result_id=result_id,
    ))


@router.patch("/installations/{installation_id}/checklist")
def update_installation_checklist(
    installation_id: str,
    data: InstallationChecklistInput,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "installations:read")),
    db: Session = Depends(get_db),
):
    installation = db.scalar(select(Installation).where(Installation.id == installation_id).with_for_update())
    if installation is None:
        raise HTTPException(404, "Orden de trabajo no encontrada.")
    if installation.status == "cancelled":
        raise HTTPException(409, "La orden fue cancelada y ya no acepta cambios de checklist.")
    if "instalador" in identity.roles:
        if not _installer_has_assignment(db, installation, identity.email or ""):
            raise HTTPException(403, "Solo puedes actualizar la lista de una orden asignada a tu cuenta.")
    elif "installations:write" not in identity.permissions:
        raise HTTPException(403, "No tienes permiso para actualizar órdenes de trabajo.")
    current = installation.checklist or []
    incoming = [item.model_dump() for item in data.checklist]
    incoming_names = [item["task"] for item in incoming]
    existing_names = [item.get("task", "") for item in current]
    if len(set(incoming_names)) != len(incoming_names) or set(incoming_names) != set(existing_names):
        raise HTTPException(422, "Actualiza únicamente las tareas que ya pertenecen a esta orden.")
    states = {item["task"]: item["done"] for item in incoming}
    updated = [{**item, "done": states[item["task"]]} for item in current]
    changed = [(old, new) for old, new in zip(current, updated) if old.get("done") != new["done"]]
    installation.checklist = updated
    for old, new in changed:
        db.add(Activity(
            customer_id=installation.customer_id,
            kind="orden de trabajo",
            note=f"{installation.folio or 'Orden'} · {new['task']}: {'completada' if new['done'] else 'reabierta'}",
            created_by=identity.email or "",
        ))
    db.commit(); db.refresh(installation)
    return _serialize(installation)


@router.get("/installers", dependencies=[Depends(require_permissions(auth_service, "installations:read"))])
def list_installers():
    with auth_service.engine.connect() as connection:
        rows = connection.execute(select(users.c.email, users.c.name).join(memberships, memberships.c.user_id == users.c.id).where(
            users.c.is_active.is_(True),
            memberships.c.organization_id == settings.organization_id,
            memberships.c.roles.contains(["instalador"]),
        ).order_by(users.c.name)).mappings().all()
    return [{"email": row["email"], "name": row["name"]} for row in rows]


@router.get("/inventory")
def list_inventory(identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:read")), db: Session = Depends(get_db)):
    items = db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all()
    reserved = {row[0]: Decimal(row[1] or 0) for row in db.execute(
        select(WorkOrderMaterial.item_id, func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity))
        .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
        .where(Installation.status.notin_(("closed", "cancelled")))
        .group_by(WorkOrderMaterial.item_id)
    ).all()}
    rows = []
    for row in items:
        held = reserved.get(row.id, Decimal("0"))
        rows.append({**_serialize_inventory_item(row, identity), "reserved_quantity": held, "available_quantity": max(Decimal(row.quantity) - held, Decimal("0"))})
    return rows


@router.post("/inventory/issue", status_code=201)
def issue_work_order_materials(data: StockIssueInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:issue")), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    installation = db.scalar(select(Installation).where(Installation.id == data.installation_id).with_for_update())
    if installation is None:
        raise HTTPException(404, "Orden de trabajo no encontrada.")
    if installation.status in {"closed", "cancelled"}:
        raise HTTPException(409, "No se puede emitir material para una orden cerrada o cancelada.")

    issued = []
    for line in data.lines:
        material = db.scalar(select(WorkOrderMaterial).where(
            WorkOrderMaterial.id == line.work_order_material_id,
            WorkOrderMaterial.installation_id == installation.id,
        ).with_for_update())
        if material is None:
            raise HTTPException(422, "El material indicado no pertenece a esta orden.")
        remaining = Decimal(str(material.requested_quantity)) - Decimal(str(material.preissued_quantity))
        if line.quantity > remaining:
            raise HTTPException(409, f"La salida excede lo solicitado para este artículo. Restante por entregar: {remaining}.")

        item = db.scalar(select(InventoryItem).where(InventoryItem.id == material.item_id).with_for_update())
        if item is None:
            raise HTTPException(404, "El artículo solicitado ya no existe en el catálogo.")
        reserved_for_other_orders = db.scalar(
            select(func.coalesce(func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity), 0))
            .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
            .where(
                WorkOrderMaterial.item_id == item.id,
                WorkOrderMaterial.installation_id != installation.id,
                Installation.status.notin_(("closed", "cancelled")),
            )
        ) or 0
        available_for_this_order = Decimal(str(item.quantity)) - Decimal(str(reserved_for_other_orders))
        if line.quantity > available_for_this_order:
            raise HTTPException(409, f"Existencia disponible para esta orden: {max(available_for_this_order, Decimal('0'))} {item.unit}.")

        item.quantity = Decimal(str(item.quantity)) - line.quantity
        material.preissued_quantity = Decimal(str(material.preissued_quantity)) + line.quantity
        reference = data.document_reference.strip()
        reason = f"Salida de solicitud {reference}" if reference else "Salida desde solicitud de materiales"
        movement = InventoryMovement(
            item_id=item.id,
            installation_id=installation.id,
            work_order_material_id=material.id,
            quantity=line.quantity,
            movement_type="out",
            unit_cost=item.unit_cost,
            reason=reason,
            created_by=identity.email or "",
        )
        db.add(movement)
        db.flush()
        issued.append({"item_id": item.id, "item_name": item.name, "quantity": float(line.quantity), "unit": item.unit, "movement_id": movement.id})

    db.commit()
    return {"installation_id": installation.id, "folio": installation.folio, "issued": issued}


@router.post("/inventory/items", status_code=201, dependencies=[Depends(require_permissions(auth_service, "inventory:manage"))])
def create_inventory_item(data: InventoryItemInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    if data.supplier_id and not db.get(Supplier, data.supplier_id):
        raise HTTPException(422, "Selecciona un proveedor registrado.")
    barcode = data.barcode.strip() if data.barcode else None
    if barcode and db.scalar(select(InventoryItem.id).where(InventoryItem.barcode == barcode)):
        raise HTTPException(409, "Ese código ya está asignado a otro artículo.")
    responsible = _validate_restock_responsible(data.restock_responsible_email, db)
    row = InventoryItem(name=data.name.strip(), description=data.description.strip(), category=data.category.strip(),
        subcategory=data.subcategory.strip(), brand=data.brand.strip(), model=data.model.strip(), supplier_id=data.supplier_id, barcode=barcode,
        unit=data.unit.strip(), quantity=data.initial_quantity, minimum_quantity=data.minimum_quantity,
        restock_responsible_email=responsible, unit_cost=data.unit_cost)
    db.add(row); db.flush()
    if data.initial_quantity:
        db.add(InventoryMovement(item_id=row.id, quantity=data.initial_quantity, movement_type="in", unit_cost=data.unit_cost, reason="existencia inicial", created_by=identity.email))
    _queue_low_stock_alert(db, background_tasks, row)
    db.commit(); db.refresh(row)
    return _serialize_inventory_item(row, identity)


@router.post("/purchases/catalog-items", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def create_purchase_catalog_item(data: PurchaseCatalogItemInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    """Create a zero-stock inventory record from an authorized purchase entry."""
    if data.supplier_id and db.get(Supplier, data.supplier_id) is None:
        raise HTTPException(422, "Selecciona un proveedor registrado.")
    barcode = data.barcode.strip() if data.barcode else None
    if barcode and db.scalar(select(InventoryItem.id).where(InventoryItem.barcode == barcode)):
        raise HTTPException(409, "Ese código ya está asignado a otro artículo.")
    row = InventoryItem(
        name=data.name.strip(), category=data.category.strip(), subcategory=data.subcategory.strip(),
        brand=data.brand.strip(), model=data.model.strip(), supplier_id=data.supplier_id,
        barcode=barcode, unit=data.unit.strip(), quantity=0, minimum_quantity=0, unit_cost=0,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Ese código ya está asignado a otro artículo.") from error
    db.refresh(row)
    return _serialize_inventory_item(row, identity)


@router.put("/inventory/items/{item_id}")
def update_inventory_item(item_id: str, data: InventoryItemUpdateInput,
                          identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:manage")),
                          db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    row = db.scalar(select(InventoryItem).where(InventoryItem.id == item_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Artículo de inventario no encontrado.")
    if data.supplier_id and not db.get(Supplier, data.supplier_id):
        raise HTTPException(422, "Selecciona un proveedor registrado.")
    responsible = _validate_restock_responsible(data.restock_responsible_email, db)
    responsible_changed = responsible != row.restock_responsible_email
    barcode = data.barcode.strip() if data.barcode else None
    if barcode and db.scalar(select(InventoryItem.id).where(
        InventoryItem.barcode == barcode, InventoryItem.id != item_id,
    )):
        raise HTTPException(409, "Ese código ya está asignado a otro artículo.")

    row.name = data.name.strip()
    row.description = data.description.strip()
    row.category = data.category.strip()
    row.subcategory = data.subcategory.strip()
    row.brand = data.brand.strip()
    row.model = data.model.strip()
    row.supplier_id = data.supplier_id
    row.barcode = barcode
    row.unit = data.unit.strip()
    row.minimum_quantity = data.minimum_quantity
    row.restock_responsible_email = responsible
    row.unit_cost = data.unit_cost
    _queue_low_stock_alert(db, background_tasks, row, force=responsible_changed)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "Ese código ya está asignado a otro artículo.") from error
    db.refresh(row)
    return _serialize_inventory_item(row, identity)


@router.post("/inventory/consume", status_code=201)
def consume_inventory(data: StockInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:write")), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    if "instalador" in identity.roles:
        installation = db.get(Installation, data.installation_id) if data.installation_id else None
        if installation is None or not _installer_has_assignment(db, installation, identity.email or ""):
            raise HTTPException(403, "Solo puedes registrar consumos en una orden asignada a tu cuenta.")
    operation = _find_offline_operation(data, "consume", identity, db)
    if operation:
        movement = db.get(InventoryMovement, operation.result_id)
        item = db.get(InventoryItem, movement.item_id) if movement else None
        if movement is None or item is None:
            raise HTTPException(409, "El registro original de esta operación ya no está disponible.")
        physical_issue = db.get(InventoryMovement, movement.related_movement_id) if movement.related_movement_id else None
        serialized_item = _serialize_inventory_item(item, identity)
        return {"movement": _serialize(movement), "physical_issue": _serialize(physical_issue) if physical_issue else None, "item": serialized_item}
    if data.installation_id:
        installation = db.scalar(select(Installation).where(Installation.id == data.installation_id).with_for_update())
        if installation is None:
            raise HTTPException(404, "Orden de trabajo no encontrada.")
        if installation.status in {"closed", "cancelled"}:
            raise HTTPException(409, "No se puede registrar consumo en una orden cerrada o cancelada.")
    item = db.scalar(select(InventoryItem).where(InventoryItem.id == data.item_id).with_for_update())
    if not item: raise HTTPException(404, "Artículo no encontrado.")
    material = db.scalar(select(WorkOrderMaterial).where(
        WorkOrderMaterial.installation_id == data.installation_id,
        WorkOrderMaterial.item_id == data.item_id,
    ).with_for_update()) if data.installation_id else None
    if data.installation_id and material is None and db.scalar(select(func.count()).select_from(WorkOrderMaterial).where(WorkOrderMaterial.installation_id == data.installation_id)):
        raise HTTPException(422, "Este material no está solicitado en la orden de trabajo.")
    stock_out = Decimal(str(data.quantity))
    if material:
        remaining = Decimal(str(material.requested_quantity)) - Decimal(str(material.consumed_quantity))
        if stock_out > remaining:
            raise HTTPException(409, f"El consumo excede lo solicitado en la orden. Restante: {remaining}.")
        from_reserved_issue = min(stock_out, max(Decimal(str(material.preissued_quantity)) - Decimal(str(material.consumed_quantity)), Decimal("0")))
        stock_out -= from_reserved_issue
        material.consumed_quantity = Decimal(str(material.consumed_quantity)) + Decimal(str(data.quantity))
        material.preissued_quantity = Decimal(str(material.preissued_quantity)) + stock_out
    if Decimal(str(item.quantity)) < stock_out:
        raise HTTPException(409, "Existencia insuficiente para este consumo.")
    item.quantity = Decimal(str(item.quantity)) - stock_out
    physical_issue = None
    if stock_out > 0:
        physical_issue = InventoryMovement(
            item_id=data.item_id, installation_id=data.installation_id,
            quantity=stock_out, movement_type="out",
            work_order_material_id=material.id if material else None,
            unit_cost=item.unit_cost, reason="Salida para consumo en orden de trabajo",
            created_by=identity.email or "",
        )
        db.add(physical_issue); db.flush()
    movement = InventoryMovement(
        item_id=data.item_id, installation_id=data.installation_id,
        quantity=data.quantity, movement_type="consumption",
        related_movement_id=physical_issue.id if physical_issue else None,
        work_order_material_id=material.id if material else None,
        unit_cost=item.unit_cost,
        reason=(data.reason.strip() or "Consumo confirmado en orden de trabajo"),
        created_by=identity.email or "",
    )
    db.add(movement); db.flush()
    _record_offline_operation(data, "consume", movement.id, identity, db)
    _queue_low_stock_alert(db, background_tasks, item)
    db.commit(); db.refresh(movement)
    serialized_item = _serialize_inventory_item(item, identity)
    return {"movement": _serialize(movement), "physical_issue": _serialize(physical_issue), "item": serialized_item}


@router.post("/inventory/receive", status_code=201)
def receive_inventory(data: StockReceiptInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:manage")), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    item = db.scalar(select(InventoryItem).where(InventoryItem.id == data.item_id).with_for_update())
    if not item: raise HTTPException(404, "Artículo no encontrado.")
    item.quantity = float(item.quantity) + data.quantity
    item.unit_cost = data.unit_cost
    movement = InventoryMovement(item_id=data.item_id, quantity=data.quantity, movement_type="in", unit_cost=data.unit_cost, reason=data.reason, created_by=identity.email)
    db.add(movement); _queue_low_stock_alert(db, background_tasks, item); db.commit(); db.refresh(movement)
    return {"movement": _serialize(movement), "item": _serialize_inventory_item(item, identity)}


@router.post("/inventory/returns", status_code=201)
def return_inventory(data: InventoryReturnInput, identity: AuthIdentity = Depends(require_any_permission(auth_service, "inventory:write", "inventory:issue")), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    source = db.scalar(select(InventoryMovement).where(InventoryMovement.id == data.out_movement_id).with_for_update())
    if source is None or source.movement_type != "out" or not source.installation_id:
        raise HTTPException(404, "No se encontró una salida de instalación válida para devolver.")
    if "instalador" in identity.roles:
        installation = db.get(Installation, source.installation_id)
        if installation is None or not _installer_has_assignment(db, installation, identity.email or ""):
            raise HTTPException(403, "Solo puedes devolver material de una orden asignada a tu cuenta.")
    operation = _find_offline_operation(data, "return", identity, db)
    if operation:
        movement = db.get(InventoryMovement, operation.result_id)
        item = db.get(InventoryItem, movement.item_id) if movement else None
        if movement is None or item is None:
            raise HTTPException(409, "El registro original de esta operación ya no está disponible.")
        serialized_item = _serialize_inventory_item(item, identity)
        serialized_movement = _serialize(movement)
        if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
            serialized_movement.pop("unit_cost", None)
        return {"movement": serialized_movement, "item": serialized_item}
    returned = db.scalar(select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(
        InventoryMovement.related_movement_id == source.id,
        InventoryMovement.movement_type.in_(["return", "damage"]),
    )) or 0
    if Decimal(str(returned)) + Decimal(str(data.quantity)) > Decimal(str(source.quantity)):
        raise HTTPException(409, "La cantidad devuelta o marcada como merma excede el material retirado en esa salida.")
    material = db.get(WorkOrderMaterial, source.work_order_material_id) if source.work_order_material_id else db.scalar(select(WorkOrderMaterial).where(
        WorkOrderMaterial.installation_id == source.installation_id,
        WorkOrderMaterial.item_id == source.item_id,
    ))
    if material:
        if source.reason.startswith("Salida para consumo"):
            returnable_planned = Decimal(str(material.consumed_quantity))
        else:
            returnable_planned = Decimal(str(material.preissued_quantity)) - Decimal(str(material.consumed_quantity))
        if Decimal(str(data.quantity)) > returnable_planned:
            raise HTTPException(409, "La devolución excede el material no consumido disponible en la orden.")
    item = db.get(InventoryItem, source.item_id)
    if item is None:
        raise HTTPException(409, "El artículo de la salida ya no existe en el catálogo.")
    is_damaged = data.condition == "damaged"
    if not is_damaged:
        item.quantity = Decimal(str(item.quantity)) + Decimal(str(data.quantity))
    movement = InventoryMovement(
        item_id=source.item_id,
        installation_id=source.installation_id,
        related_movement_id=source.id,
        work_order_material_id=material.id if material else None,
        quantity=data.quantity,
        movement_type="damage" if is_damaged else "return",
        unit_cost=source.unit_cost,
        reason=data.reason.strip() or ("Merma de material dañado" if is_damaged else "Devolución de material sobrante"),
        created_by=identity.email or "",
    )
    if is_damaged and not source.reason.startswith("Salida para consumo"):
        if material:
            material.consumed_quantity = Decimal(str(material.consumed_quantity)) + Decimal(str(data.quantity))
        db.add(InventoryMovement(
            item_id=source.item_id,
            installation_id=source.installation_id,
            related_movement_id=source.id,
            work_order_material_id=material.id if material else None,
            quantity=data.quantity,
            movement_type="consumption",
            unit_cost=source.unit_cost,
            reason="Consumo por merma de material dañado",
            created_by=identity.email or "",
        ))
    if material:
        if not is_damaged:
            material.preissued_quantity = Decimal(str(material.preissued_quantity)) - Decimal(str(data.quantity))
        if source.reason.startswith("Salida para consumo") and not is_damaged:
            material.consumed_quantity = Decimal(str(material.consumed_quantity)) - Decimal(str(data.quantity))
            consumption = db.scalar(select(InventoryMovement).where(
                InventoryMovement.related_movement_id == source.id,
                InventoryMovement.movement_type == "consumption",
            ).with_for_update())
            if consumption is not None:
                db.add(InventoryMovement(
                    item_id=source.item_id,
                    installation_id=source.installation_id,
                    related_movement_id=consumption.id,
                    work_order_material_id=material.id,
                    quantity=data.quantity,
                    movement_type="consumption_return",
                    unit_cost=source.unit_cost,
                    reason="Consumo corregido por devolución de sobrante",
                    created_by=identity.email or "",
                ))
    db.add(movement); db.flush()
    _record_offline_operation(data, "return", movement.id, identity, db)
    _queue_low_stock_alert(db, background_tasks, item)
    db.commit(); db.refresh(movement)
    serialized_item = _serialize_inventory_item(item, identity)
    serialized_movement = _serialize(movement)
    if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
        serialized_item.pop("unit_cost", None)
        serialized_movement.pop("unit_cost", None)
    return {"movement": serialized_movement, "item": serialized_item}


@router.get("/inventory/movements")
def list_inventory_movements(
    item_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 500,
    offset: int = 0,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:read")),
    db: Session = Depends(get_db),
):
    if limit < 1 or limit > 500 or offset < 0:
        raise HTTPException(422, "La página debe tener entre 1 y 500 movimientos y un desplazamiento no negativo.")
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "La fecha inicial debe ser anterior a la fecha final.")
    return_rows = aliased(InventoryMovement)
    returned_total = select(func.coalesce(func.sum(return_rows.quantity), 0)).where(
        return_rows.related_movement_id == InventoryMovement.id,
        return_rows.movement_type.in_(["return", "damage"]),
    ).correlate(InventoryMovement).scalar_subquery()
    query = select(InventoryMovement, InventoryItem.name, InventoryItem.unit, returned_total.label("returned_quantity")).join(
        InventoryItem, InventoryItem.id == InventoryMovement.item_id
    )
    if item_id:
        query = query.where(InventoryMovement.item_id == item_id)
    if from_date:
        query = query.where(InventoryMovement.created_at >= datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc))
    if to_date:
        query = query.where(InventoryMovement.created_at < datetime.combine(to_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    if "instalador" in identity.roles:
        assigned_ids = select(InstallationAssignment.installation_id).where(
            func.lower(InstallationAssignment.installer_email) == (identity.email or "").strip().lower()
        )
        query = query.join(Installation, Installation.id == InventoryMovement.installation_id).where(or_(
            func.lower(Installation.lead_installer) == (identity.email or "").strip().lower(),
            Installation.id.in_(assigned_ids),
        ))
    query = query.order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc()).limit(limit).offset(offset)
    rows = db.execute(query).all()
    result = []
    for movement, item_name, unit, returned_quantity in rows:
        line = _serialize(movement)
        line.update({"item_name": item_name, "unit": unit, "signed_quantity": -float(movement.quantity) if movement.movement_type in {"out", "waste"} else (0.0 if movement.movement_type in {"consumption", "consumption_return", "damage"} else float(movement.quantity))})
        if movement.movement_type == "out":
            line["returnable_quantity"] = max(0.0, float(movement.quantity) - float(returned_quantity or 0))
        if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
            line.pop("unit_cost", None)
        result.append(line)
    return result


@router.post("/expenses", status_code=201)
def add_expense(data: ExpenseInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "expenses:write")), db: Session = Depends(get_db)):
    installation = db.get(Installation, data.installation_id) if data.installation_id else None
    if data.installation_id and not installation: raise HTTPException(404, "Instalación no encontrada.")
    if "instalador" in identity.roles and (installation is None or not _installer_has_assignment(db, installation, identity.email or "")):
        raise HTTPException(403, "Selecciona una orden asignada a tu cuenta para registrar gastos de campo.")
    project = db.get(Project, data.project_id) if data.project_id else None
    if data.project_id and project is None: raise HTTPException(404, "Proyecto no encontrado.")
    if installation and data.project_id and installation.project_id != data.project_id:
        raise HTTPException(422, "El proyecto seleccionado no corresponde a la orden de trabajo.")
    if installation:
        data.project_id = installation.project_id
    elif project is None and "instalador" in identity.roles:
        raise HTTPException(422, "Selecciona una orden asignada para vincular el gasto a su proyecto.")
    if installation and installation.status == "cancelled": raise HTTPException(409, "No se puede registrar un gasto en una orden cancelada.")
    operation = _find_offline_operation(data, "expense", identity, db)
    if operation:
        row = db.get(ProjectExpense, operation.result_id)
        if row is None:
            raise HTTPException(409, "El registro original de esta operación ya no está disponible.")
        account = db.get(FinancialAccount, row.account_id) if row.account_id else None
        result = _serialize(row)
        result.pop("receipt_drive_file_id", None)
        result["receipt_available"] = bool(row.receipt_drive_file_id or row.receipt_url)
        result["receipt_drive_available"] = bool(row.receipt_drive_file_id)
        result["receipt_filename"] = row.receipt_filename or None
        result["account_name"] = account.name if account else None
        return result
    if "instalador" not in identity.roles and not data.account_id:
        raise HTTPException(422, "Selecciona la cuenta de caja o banco que pagó este gasto.")
    account = None
    if data.account_id:
        account = db.scalar(select(FinancialAccount).where(FinancialAccount.id == data.account_id, FinancialAccount.active.is_(True)).with_for_update())
        if account is None: raise HTTPException(404, "Selecciona una cuenta de caja o banco activa.")
    row = ProjectExpense(**data.model_dump(exclude={"operation_id"}), created_by=identity.email); db.add(row); db.flush()
    if account:
        movement = CashMovement(account_id=account.id, direction="out", amount=data.amount,
            category=f"Gasto · {data.category}", description=data.description,
            occurred_on=data.occurred_on, source_type="expense", source_id=row.id,
            created_by=identity.email or "")
        db.add(movement)
    _record_offline_operation(data, "expense", row.id, identity, db)
    db.commit(); db.refresh(row)
    result = _serialize(row)
    result.pop("receipt_drive_file_id", None)
    result["receipt_available"] = bool(row.receipt_drive_file_id or row.receipt_url)
    result["receipt_drive_available"] = bool(row.receipt_drive_file_id)
    result["receipt_filename"] = row.receipt_filename or None
    result["account_name"] = account.name if account else None
    return result


@router.get("/expenses", dependencies=[Depends(require_permissions(auth_service, "expenses:read"))])
def list_expenses(db: Session = Depends(get_db)):
    rows = db.scalars(select(ProjectExpense).order_by(ProjectExpense.occurred_on.desc(), ProjectExpense.created_at.desc())).all()
    result = []
    for row in rows:
        item = _serialize(row)
        account = db.get(FinancialAccount, row.account_id) if row.account_id else None
        item["account_name"] = account.name if account else None
        item["can_reverse"] = row.reversal_of_id is None and db.scalar(
            select(ProjectExpense.id).where(ProjectExpense.reversal_of_id == row.id)
        ) is None
        item["receipt_available"] = bool(row.receipt_drive_file_id or row.receipt_url)
        item["receipt_drive_available"] = bool(row.receipt_drive_file_id)
        item["receipt_filename"] = row.receipt_filename or None
        item.pop("receipt_drive_file_id", None)
        installation = db.get(Installation, row.installation_id) if row.installation_id else None
        customer = db.get(Customer, installation.customer_id) if installation else None
        linked_project_id = row.project_id or (installation.project_id if installation else None)
        project = db.get(Project, linked_project_id) if linked_project_id else None
        item["project_customer"] = project.name if project else (customer.name if customer else "Gasto operativo")
        item["project_code"] = project.code if project else ""
        item["project_city"] = customer.city if customer else ""
        result.append(item)
    return result


@router.put("/expenses/{expense_id}/receipt-file")
async def upload_expense_receipt_file(
    expense_id: str,
    request: Request,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "expenses:write")),
    db: Session = Depends(get_db),
):
    expense = db.get(ProjectExpense, expense_id)
    if expense is None:
        raise HTTPException(404, "Gasto no encontrado.")
    if "instalador" in identity.roles:
        installation = db.get(Installation, expense.installation_id) if expense.installation_id else None
        if installation is None or not _installer_has_assignment(db, installation, identity.email or ""):
            raise HTTPException(403, "Solo puedes adjuntar comprobantes a gastos de tus órdenes asignadas.")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    file_type = _EXPENSE_RECEIPT_TYPES.get(content_type)
    if file_type is None:
        raise HTTPException(415, "Adjunta un comprobante PDF, JPG, PNG o WebP.")
    try:
        declared_length = int(request.headers.get("content-length", "0"))
    except ValueError:
        raise HTTPException(400, "Tamaño de archivo no válido.") from None
    if declared_length > _MAX_MATERIAL_REQUEST_BYTES:
        raise HTTPException(413, "El comprobante debe pesar 12 MB o menos.")
    collected = bytearray()
    async for chunk in request.stream():
        if len(collected) + len(chunk) > _MAX_MATERIAL_REQUEST_BYTES:
            raise HTTPException(413, "El comprobante debe pesar 12 MB o menos.")
        collected.extend(chunk)
    content = bytes(collected)
    if not content:
        raise HTTPException(400, "El archivo está vacío.")
    if not content.startswith(file_type[1]) or (content_type == "image/webp" and content[8:12] != b"WEBP"):
        raise HTTPException(415, "El contenido del comprobante no coincide con su formato.")
    raw_name = unquote(request.headers.get("x-document-name", "comprobante"))
    raw_name = raw_name.replace("\\", "/").split("/")[-1]
    filename = re.sub(r"[^\w.() -]", "_", raw_name, flags=re.UNICODE).strip(" .")[:220] or "comprobante"
    extension = file_type[0]
    if not filename.lower().endswith(extension):
        filename = f"{filename.rsplit('.', 1)[0] if '.' in filename else filename}{extension}"
    try:
        drive_id = save_private_file(
            filename=f"gasto-{expense.id}-{filename}", content=content,
            content_type=content_type, existing_file_id=expense.receipt_drive_file_id,
        )
    except RuntimeError as error:
        if str(error) == "not_configured":
            raise HTTPException(503, "drive_not_configured") from None
        raise HTTPException(502, "No se pudo archivar el comprobante en Drive.") from None
    except Exception:
        raise HTTPException(502, "No se pudo archivar el comprobante en Drive.") from None
    expense.receipt_drive_file_id = drive_id
    expense.receipt_filename = filename
    expense.receipt_content_type = content_type
    expense.receipt_updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"saved": True, "filename": filename, "content_type": content_type, "updated_at": expense.receipt_updated_at.isoformat()}


@router.get("/expenses/{expense_id}/receipt-file")
def get_expense_receipt_file(
    expense_id: str,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "expenses:read")),
    db: Session = Depends(get_db),
):
    expense = db.get(ProjectExpense, expense_id)
    if expense is None:
        raise HTTPException(404, "Gasto no encontrado.")
    if not expense.receipt_drive_file_id:
        raise HTTPException(404, "Este gasto no tiene un comprobante archivado.")
    try:
        stored = download_private_file(expense.receipt_drive_file_id)
    except Exception:
        raise HTTPException(502, "No se pudo recuperar el comprobante archivado.") from None
    filename = expense.receipt_filename or "comprobante"
    return Response(
        content=stored.content, media_type=expense.receipt_content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{urlquote(filename)}"},
    )


@router.post("/expenses/{expense_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "expenses:write"))])
def reverse_expense(expense_id: str, data: PaymentCorrectionInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if "instalador" in identity.roles:
        raise HTTPException(403, "Solo administración o contabilidad puede corregir gastos registrados.")
    original = db.scalar(select(ProjectExpense).where(ProjectExpense.id == expense_id).with_for_update())
    if original is None:
        raise HTTPException(404, "Gasto no encontrado.")
    if original.reversal_of_id is not None:
        raise HTTPException(409, "Una corrección no puede revertirse; registra un nuevo gasto si corresponde.")
    if db.scalar(select(ProjectExpense.id).where(ProjectExpense.reversal_of_id == original.id)):
        raise HTTPException(409, "Este gasto ya tiene una corrección registrada.")

    original_cash = db.scalars(select(CashMovement).where(
        CashMovement.source_type == "expense", CashMovement.source_id == original.id,
    ).with_for_update()).all()
    if original.account_id and len(original_cash) != 1:
        raise HTTPException(409, "No se puede corregir: el gasto no tiene exactamente un movimiento de caja/banco relacionado.")
    if not original.account_id and original_cash:
        raise HTTPException(409, "El gasto de campo tiene un movimiento de caja inesperado; revisa el origen antes de corregirlo.")
    if original_cash and db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == original_cash[0].id)):
        raise HTTPException(409, "El movimiento de cuenta ya tiene una reversa registrada; revisa el historial.")

    correction = ProjectExpense(
        installation_id=original.installation_id,
        category=original.category,
        expense_type=original.expense_type,
        description=f"Corrección del gasto {original.id}: {data.reason}",
        amount=-Decimal(original.amount),
        occurred_on=date.today(),
        receipt_url="",
        account_id=original.account_id,
        created_by=identity.email or "",
        reversal_of_id=original.id,
    )
    db.add(correction)
    db.flush()
    if original_cash:
        movement = original_cash[0]
        db.add(CashMovement(
            account_id=movement.account_id,
            direction="in",
            amount=movement.amount,
            category="Corrección de gasto",
            description=f"Corrección del gasto {original.id}: {data.reason}",
            occurred_on=date.today(),
            source_type="expense_reversal",
            source_id=original.id,
            reversal_of_id=movement.id,
            created_by=identity.email or "",
        ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Este gasto ya tiene una corrección registrada.")
    db.refresh(correction)
    account = db.get(FinancialAccount, correction.account_id) if correction.account_id else None
    result = _serialize(correction)
    result["account_name"] = account.name if account else None
    return result


@router.get("/accounts", dependencies=[Depends(require_permissions(auth_service, "accounts:read"))])
def list_financial_accounts(db: Session = Depends(get_db)):
    result = []
    for account in db.scalars(select(FinancialAccount).where(FinancialAccount.active.is_(True)).order_by(FinancialAccount.name)).all():
        movements = db.scalars(select(CashMovement).where(CashMovement.account_id == account.id)).all()
        balance = Decimal(account.opening_balance) + sum(
            (Decimal(movement.amount) if movement.direction == "in" else -Decimal(movement.amount) for movement in movements),
            Decimal("0"),
        )
        result.append({**_serialize(account), "current_balance": balance, "movement_count": len(movements)})
    return result


@router.post("/accounts", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:manage"))])
def create_financial_account(data: FinancialAccountInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = FinancialAccount(**data.model_dump(), created_by=identity.email or "")
    db.add(row); db.commit(); db.refresh(row)
    return {**_serialize(row), "current_balance": Decimal(row.opening_balance), "movement_count": 0}


@router.get("/accounts/{account_id}/movements", dependencies=[Depends(require_permissions(auth_service, "accounts:read"))])
def list_account_movements(account_id: str, db: Session = Depends(get_db)):
    account = db.get(FinancialAccount, account_id)
    if account is None:
        raise HTTPException(404, "Cuenta financiera no encontrada.")
    movements = db.scalars(select(CashMovement).where(CashMovement.account_id == account_id).order_by(CashMovement.occurred_on.desc(), CashMovement.created_at.desc())).all()
    return {
        "account": _serialize(account),
        "opening_balance": Decimal(account.opening_balance),
        "opening_balance_date": account.opening_balance_date,
        "movements": [_serialize(item) for item in movements],
    }


@router.post("/cash-movements", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:write"))])
def create_cash_movement(data: CashMovementInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    account = db.get(FinancialAccount, data.account_id)
    if account is None or not account.active:
        raise HTTPException(404, "Selecciona una cuenta activa.")
    row = CashMovement(**data.model_dump(), source_type="manual", created_by=identity.email or "")
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.post("/cash-transfers", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:write"))])
def create_cash_transfer(data: CashTransferInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if data.source_account_id == data.destination_account_id:
        raise HTTPException(422, "Selecciona dos cuentas distintas para la transferencia.")
    accounts = db.scalars(select(FinancialAccount).where(
        FinancialAccount.id.in_([data.source_account_id, data.destination_account_id]),
    ).order_by(FinancialAccount.id).with_for_update()).all()
    by_id = {account.id: account for account in accounts}
    source = by_id.get(data.source_account_id)
    destination = by_id.get(data.destination_account_id)
    if source is None or destination is None or not source.active or not destination.active:
        raise HTTPException(404, "Selecciona dos cuentas activas.")
    if data.occurred_on < max(source.opening_balance_date, destination.opening_balance_date):
        raise HTTPException(422, "La fecha no puede ser anterior al saldo inicial de ambas cuentas.")
    transfer_id = str(uuid4())
    rows = [
        CashMovement(
            account_id=source.id, direction="out", amount=data.amount,
            category=f"Transferencia a {destination.name}", description=data.description,
            occurred_on=data.occurred_on, source_type="transfer", source_id=transfer_id,
            created_by=identity.email or "",
        ),
        CashMovement(
            account_id=destination.id, direction="in", amount=data.amount,
            category=f"Transferencia desde {source.name}", description=data.description,
            occurred_on=data.occurred_on, source_type="transfer", source_id=transfer_id,
            created_by=identity.email or "",
        ),
    ]
    db.add_all(rows); db.commit()
    for row in rows:
        db.refresh(row)
    return {"transfer_id": transfer_id, "movements": [_serialize(row) for row in rows]}


@router.post("/cash-movements/{movement_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:write"))])
def reverse_cash_movement(movement_id: str, data: PaymentCorrectionInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    original = db.scalar(select(CashMovement).where(CashMovement.id == movement_id).with_for_update())
    if original is None:
        raise HTTPException(404, "Movimiento de cuenta no encontrado.")
    if original.source_type in {"supplier_payment", "customer_payment"}:
        raise HTTPException(409, "Corrige este pago desde su compra o cuenta por cobrar para actualizar también el saldo relacionado.")
    if original.source_type not in {"manual", "transfer"}:
        raise HTTPException(409, "Este movimiento está ligado a otra operación; corrígelo desde su origen para conservar sus efectos relacionados.")
    if original.reversal_of_id is not None:
        raise HTTPException(409, "Una reversa no puede revertirse; registra un nuevo movimiento de corrección.")
    if original.source_type == "transfer":
        pair = db.scalars(select(CashMovement).where(
            CashMovement.source_type == "transfer", CashMovement.source_id == original.source_id,
        ).with_for_update()).all()
        if len(pair) != 2:
            raise HTTPException(409, "La transferencia no conserva sus dos movimientos relacionados.")
        if any(db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == row.id)) for row in pair):
            raise HTTPException(409, "Esta transferencia ya tiene una reversa registrada.")
        reversals = [CashMovement(
            account_id=row.account_id,
            direction="out" if row.direction == "in" else "in",
            amount=row.amount,
            category="Reversa de transferencia",
            description=f"Reversa de transferencia {original.source_id}: {data.reason}",
            occurred_on=date.today(), source_type="transfer_reversal", source_id=original.source_id,
            reversal_of_id=row.id, created_by=identity.email or "",
        ) for row in pair]
        db.add_all(reversals); db.commit()
        for row in reversals:
            db.refresh(row)
        return {"transfer_id": original.source_id, "movements": [_serialize(row) for row in reversals]}
    if db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == movement_id)):
        raise HTTPException(409, "Este movimiento ya tiene una reversa registrada.")
    reversal = CashMovement(
        account_id=original.account_id,
        direction="out" if original.direction == "in" else "in",
        amount=original.amount,
        category="Corrección",
        description=f"Reversa del movimiento {original.id}: {data.reason}",
        occurred_on=date.today(),
        source_type="reversal",
        source_id=original.id,
        reversal_of_id=original.id,
        created_by=identity.email or "",
    )
    db.add(reversal); db.commit(); db.refresh(reversal)
    return _serialize(reversal)


@router.get("/suppliers", dependencies=[Depends(require_permissions(auth_service, "suppliers:read"))])
def list_suppliers(db: Session = Depends(get_db)):
    rows = db.scalars(select(Supplier).order_by(Supplier.name)).all()
    results = []
    for row in rows:
        gross = Decimal(db.scalar(select(func.coalesce(func.sum(Purchase.total - Purchase.paid_amount), 0)).where(Purchase.supplier_id == row.id)) or 0)
        corrected = Decimal(db.scalar(select(func.coalesce(func.sum(PurchaseCorrection.amount), 0))
            .join(Purchase, Purchase.id == PurchaseCorrection.purchase_id).where(Purchase.supplier_id == row.id)) or 0)
        results.append({**_serialize(row), "current_balance": gross - corrected})
    return results


@router.post("/suppliers", status_code=201, dependencies=[Depends(require_permissions(auth_service, "suppliers:manage"))])
def create_supplier(data: SupplierInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    values = data.model_dump()
    values["name"] = values["name"].strip()
    values["rfc"] = values["rfc"].strip().upper()
    values["email"] = values["email"].strip().lower()
    if values["payment_terms"] == "cash":
        values["credit_days"] = 0
    row = Supplier(**values, created_by=identity.email or "")
    db.add(row); db.commit(); db.refresh(row)
    return {**_serialize(row), "current_balance": Decimal("0")}


def _purchase_result(db: Session, purchase: Purchase):
    supplier = db.get(Supplier, purchase.supplier_id)
    lines = db.scalars(select(PurchaseLine).where(PurchaseLine.purchase_id == purchase.id)).all()
    inventory_items = {item.id: item.name for item in db.scalars(
        select(InventoryItem).where(InventoryItem.id.in_([line.item_id for line in lines]))
    ).all()} if lines else {}
    payments = db.scalars(select(SupplierPayment).where(SupplierPayment.purchase_id == purchase.id).order_by(SupplierPayment.paid_on, SupplierPayment.created_at)).all()
    correction = db.scalar(select(PurchaseCorrection).where(PurchaseCorrection.purchase_id == purchase.id))
    reversed_payment_ids = {row[0] for row in db.execute(select(SupplierPayment.reversal_of_id).where(SupplierPayment.reversal_of_id.is_not(None))).all()}
    return {
        **_serialize(purchase),
        "status": "corrected" if correction else purchase.status,
        "supplier": {"id": supplier.id, "name": supplier.name} if supplier else None,
        "balance": Decimal("0") if correction else Decimal(purchase.total) - Decimal(purchase.paid_amount),
        "correction": _serialize(correction) if correction else None,
        "can_reverse": correction is None,
        "lines": [
            {**_serialize(line), "item_name": inventory_items.get(line.item_id, "Artículo")}
            for line in lines
        ],
        "payments": [{**_serialize(payment), "is_reversal": payment.reversal_of_id is not None,
            "can_reverse": payment.reversal_of_id is None and payment.id not in reversed_payment_ids}
            for payment in payments],
    }


def _record_supplier_payment(db: Session, purchase: Purchase, amount: Decimal, account_id: str, paid_on: date, reference: str, email: str):
    account = db.scalar(select(FinancialAccount).where(FinancialAccount.id == account_id, FinancialAccount.active.is_(True)).with_for_update())
    if account is None:
        raise HTTPException(404, "Selecciona una cuenta de caja o banco activa para registrar el pago.")
    cash = CashMovement(
        account_id=account.id,
        direction="out",
        amount=amount,
        category="Pago a proveedor",
        description=f"Pago a {db.get(Supplier, purchase.supplier_id).name} · {purchase.folio}",
        occurred_on=paid_on,
        source_type="supplier_payment",
        created_by=email,
    )
    db.add(cash); db.flush()
    payment = SupplierPayment(
        purchase_id=purchase.id,
        account_id=account.id,
        cash_movement_id=cash.id,
        amount=amount,
        paid_on=paid_on,
        reference=reference.strip(),
        created_by=email,
    )
    db.add(payment); db.flush()
    cash.source_id = payment.id
    purchase.paid_amount = Decimal(purchase.paid_amount) + amount
    purchase.status = "paid" if purchase.paid_amount >= purchase.total else "partially_paid"
    return payment


def _parse_purchase_cfdi_xml(raw_xml: str) -> dict:
    """Parse a CFDI invoice into a review proposal only; never persist source XML or post inventory here."""
    if len(raw_xml.encode("utf-8")) > 2 * 1024 * 1024:
        raise HTTPException(413, "El XML excede el límite de 2 MiB.")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", raw_xml, re.IGNORECASE):
        raise HTTPException(422, "El XML no debe declarar DTD ni entidades externas.")
    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as exc:
        raise HTTPException(422, "El archivo no contiene un XML CFDI válido.") from exc
    if root.tag.rsplit("}", 1)[-1] != "Comprobante":
        raise HTTPException(422, "El XML debe tener un comprobante CFDI como raíz.")

    def attribute(node: ET.Element | None, name: str, default: str = "") -> str:
        if node is None:
            return default
        return node.attrib.get(name, node.attrib.get(name.lower(), default))

    def first(local_name: str, parent: ET.Element = root) -> ET.Element | None:
        return next((node for node in parent.iter() if node.tag.rsplit("}", 1)[-1] == local_name), None)

    version = attribute(root, "Version")
    if version not in {"3.3", "4.0"}:
        raise HTTPException(422, "Se admiten CFDI 3.3 y 4.0.")
    if attribute(root, "TipoDeComprobante").upper() != "I":
        raise HTTPException(422, "Solo se admiten CFDI de ingreso por compra; no notas de crédito ni complementos de pago.")
    currency = attribute(root, "Moneda", "MXN").upper()
    if currency != "MXN":
        raise HTTPException(422, "La compra solo se puede prellenar con facturas en MXN.")

    emitter = first("Emisor")
    issuer_rfc = attribute(emitter, "Rfc", attribute(emitter, "rfc")).strip().upper()
    issuer_name = attribute(emitter, "Nombre", attribute(emitter, "nombre")).strip()
    if not issuer_rfc:
        raise HTTPException(422, "El XML no incluye el RFC del proveedor emisor.")

    stamp = first("TimbreFiscalDigital")
    invoice_reference = attribute(stamp, "UUID").strip().upper()
    if not invoice_reference:
        series, folio = attribute(root, "Serie").strip(), attribute(root, "Folio").strip()
        invoice_reference = f"{series}-{folio}".strip("-")
    if not invoice_reference:
        raise HTTPException(422, "El CFDI no tiene UUID ni referencia de serie/folio.")

    raw_date = attribute(root, "Fecha")
    try:
        purchase_date = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).date().isoformat()
    except ValueError as exc:
        raise HTTPException(422, "La fecha de emisión del CFDI no es válida.") from exc

    def decimal_attr(node: ET.Element, name: str, *, required: bool = True) -> Decimal:
        raw_value = attribute(node, name)
        if not raw_value and not required:
            return Decimal("0")
        try:
            value = Decimal(raw_value)
        except (InvalidOperation, ValueError) as exc:
            raise HTTPException(422, f"El campo {name} no contiene un importe válido.") from exc
        if not value.is_finite() or len(value.as_tuple().digits) > 24 or value.adjusted() > 14 or value.as_tuple().exponent < -8:
            raise HTTPException(422, f"El campo {name} no contiene un importe válido.")
        return value

    concepts = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "Concepto"]
    if not concepts or len(concepts) > 100:
        raise HTTPException(422, "El CFDI debe contener entre 1 y 100 conceptos.")
    lines = []
    for concept in concepts:
        quantity = decimal_attr(concept, "Cantidad")
        amount = decimal_attr(concept, "Importe", required=False)
        discount = decimal_attr(concept, "Descuento", required=False)
        unit_price = decimal_attr(concept, "ValorUnitario", required=False)
        if quantity <= 0:
            raise HTTPException(422, "El CFDI contiene una cantidad no válida.")
        # Import is the source line amount; subtract its explicit line discount.
        net_amount = amount - discount if amount else quantity * unit_price - discount
        if net_amount <= 0:
            raise HTTPException(422, "El CFDI contiene un concepto con importe neto no positivo.")
        unit_cost = (net_amount / quantity).quantize(Decimal("0.01"))
        lines.append({
            "identifier": attribute(concept, "NoIdentificacion").strip(),
            "product_service_key": attribute(concept, "ClaveProdServ").strip(),
            "description": attribute(concept, "Descripcion").strip(),
            "quantity": quantity,
            "unit": attribute(concept, "Unidad", attribute(concept, "ClaveUnidad", "pieza")).strip() or "pieza",
            "net_line_amount": net_amount,
            "unit_cost_before_global_adjustments": unit_cost,
        })

    subtotal = decimal_attr(root, "SubTotal", required=False)
    global_discount = decimal_attr(root, "Descuento", required=False)
    invoice_total = decimal_attr(root, "Total")
    if subtotal < 0 or global_discount < 0 or invoice_total < 0:
        raise HTTPException(422, "El CFDI contiene totales negativos no admitidos.")
    return {
        "version": version,
        "invoice_reference": invoice_reference,
        "purchase_date": purchase_date,
        "currency": currency,
        "supplier_rfc": issuer_rfc,
        "supplier_name": issuer_name,
        "declared_subtotal": subtotal,
        "global_discount": global_discount,
        "declared_total": invoice_total,
        "concepts": lines,
        "review_only": True,
        "source_xml_stored": False,
        "requires_accounting_review": bool(global_discount or invoice_total != subtotal - global_discount),
    }


@router.post("/purchases/parse-cfdi", dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def parse_purchase_cfdi(data: PurchaseInvoiceXmlInput):
    """Read a local user's CFDI into a proposal that must be reviewed before posting a purchase."""
    return _parse_purchase_cfdi_xml(data.xml)


@router.get("/purchases", dependencies=[Depends(require_permissions(auth_service, "purchases:read"))])
def list_purchases(db: Session = Depends(get_db)):
    return [_purchase_result(db, row) for row in db.scalars(select(Purchase).order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())).all()]


_PURCHASE_INVOICE_TYPES = {
    "application/pdf": (".pdf", b"%PDF-"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}
_PURCHASE_INVOICE_MAX_BYTES = 12 * 1024 * 1024


@router.put("/purchases/{purchase_id}/invoice-file")
async def upload_purchase_invoice_file(
    purchase_id: str,
    request: Request,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "purchases:write")),
    db: Session = Depends(get_db),
):
    purchase = db.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(404, "Compra no encontrada.")
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    invoice_type = _PURCHASE_INVOICE_TYPES.get(content_type)
    if content_type in {"application/xml", "text/xml"}:
        invoice_type = (".xml", b"")
    if invoice_type is None:
        raise HTTPException(415, "Adjunta el XML CFDI, un PDF o una foto JPG, PNG o WebP.")
    try:
        declared_length = int(request.headers.get("content-length", "0"))
    except ValueError:
        raise HTTPException(400, "Tamaño de archivo no válido.") from None
    max_bytes = 2 * 1024 * 1024 if invoice_type[0] == ".xml" else _PURCHASE_INVOICE_MAX_BYTES
    if declared_length > max_bytes:
        raise HTTPException(413, "El XML debe pesar hasta 2 MiB; PDF y fotos hasta 12 MiB.")
    collected = bytearray()
    async for chunk in request.stream():
        if len(collected) + len(chunk) > max_bytes:
            raise HTTPException(413, "El XML debe pesar hasta 2 MiB; PDF y fotos hasta 12 MiB.")
        collected.extend(chunk)
    content = bytes(collected)
    if not content:
        raise HTTPException(400, "El archivo está vacío.")
    if invoice_type[0] == ".xml":
        try:
            xml_text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(415, "El XML CFDI debe estar codificado en UTF-8.") from None
        if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
            raise HTTPException(415, "El XML CFDI contiene declaraciones no permitidas.")
        _parse_purchase_cfdi_xml(xml_text)
    elif not content.startswith(invoice_type[1]) or (content_type == "image/webp" and content[8:12] != b"WEBP"):
        raise HTTPException(415, "El contenido del archivo no coincide con su formato.")
    raw_name = unquote(request.headers.get("x-document-name", "factura"))
    raw_name = raw_name.replace("\\", "/").split("/")[-1]
    filename = re.sub(r"[^\w.() -]", "_", raw_name, flags=re.UNICODE).strip(" .")[:220]
    if not filename:
        filename = "factura"
    extension = invoice_type[0]
    if not filename.lower().endswith(extension):
        filename = f"{filename.rsplit('.', 1)[0] if '.' in filename else filename}{extension}"
    try:
        drive_id = save_private_file(
            filename=f"{purchase.folio}-{filename}",
            content=content,
            content_type=content_type,
            existing_file_id=purchase.invoice_drive_file_id,
        )
    except RuntimeError as error:
        if str(error) == "not_configured":
            raise HTTPException(503, "drive_not_configured") from None
        raise HTTPException(502, "No se pudo archivar la factura en Drive.") from None
    except Exception:
        raise HTTPException(502, "No se pudo archivar la factura en Drive.") from None
    purchase.invoice_drive_file_id = drive_id
    purchase.invoice_filename = filename
    purchase.invoice_content_type = content_type
    purchase.invoice_updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"saved": True, "filename": filename, "content_type": content_type, "updated_at": purchase.invoice_updated_at.isoformat()}


@router.get("/purchases/{purchase_id}/invoice-file")
def get_purchase_invoice_file(
    purchase_id: str,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "purchases:read")),
    db: Session = Depends(get_db),
):
    purchase = db.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(404, "Compra no encontrada.")
    if not purchase.invoice_drive_file_id:
        raise HTTPException(404, "Esta compra no tiene una factura archivada.")
    try:
        stored = download_private_file(purchase.invoice_drive_file_id)
    except Exception:
        raise HTTPException(502, "No se pudo recuperar la factura archivada.") from None
    filename = purchase.invoice_filename or "factura"
    return Response(
        content=stored.content,
        media_type=purchase.invoice_content_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{urlquote(filename)}"},
    )


@router.post("/purchases", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def create_purchase(data: PurchaseInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    supplier = db.scalar(select(Supplier).where(Supplier.id == data.supplier_id, Supplier.active.is_(True)))
    if supplier is None:
        raise HTTPException(404, "Selecciona un proveedor activo.")
    if data.payment_terms == "credit" and supplier.credit_days < 1:
        raise HTTPException(422, "El proveedor debe tener días de crédito configurados para registrar esta compra a crédito.")
    due_date = data.due_date
    if data.payment_terms == "credit":
        due_date = due_date or date.fromordinal(data.purchase_date.toordinal() + supplier.credit_days)
        if due_date < data.purchase_date:
            raise HTTPException(422, "La fecha de vencimiento no puede ser anterior a la compra.")
    elif due_date is not None:
        raise HTTPException(422, "Una compra de contado no lleva fecha de vencimiento.")

    locked_lines = []
    total = Decimal("0")
    for line in data.lines:
        item = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id).with_for_update())
        if item is None:
            raise HTTPException(404, "Uno de los artículos seleccionados ya no existe en almacén.")
        line_total = (line.quantity * line.unit_cost).quantize(Decimal("0.01"))
        total += line_total
        locked_lines.append((line, item, line_total))
    total = total.quantize(Decimal("0.01"))
    if data.initial_payment > total:
        raise HTTPException(422, "El pago inicial excede el total de la compra.")
    if data.payment_terms == "cash" and data.initial_payment != total:
        raise HTTPException(422, "Una compra de contado debe quedar pagada al registrarse; indica el total y la cuenta usada.")
    if data.initial_payment and not data.payment_account_id:
        raise HTTPException(422, "Selecciona la cuenta usada para el pago inicial.")
    if not data.initial_payment and data.payment_account_id:
        raise HTTPException(422, "No indiques una cuenta bancaria si no se registrará un pago inicial.")
    if data.initial_payment:
        payment_account = db.scalar(select(FinancialAccount).where(
            FinancialAccount.id == data.payment_account_id,
            FinancialAccount.active.is_(True),
        ).with_for_update())
        if payment_account is None:
            raise HTTPException(404, "Selecciona una cuenta de caja o banco activa para registrar el pago inicial.")

    if db.get_bind().dialect.name == "postgresql":
        sequence = db.execute(text("SELECT nextval('ae_purchase_folio_seq')")).scalar_one()
    else:
        sequence = (db.scalar(select(func.count()).select_from(Purchase)) or 0) + 1
    purchase = Purchase(
        folio=f"AE-C-{datetime.now(timezone.utc).year}-{sequence:05d}",
        supplier_id=supplier.id,
        invoice_number=data.invoice_number.strip(),
        payment_terms=data.payment_terms,
        purchase_date=data.purchase_date,
        due_date=due_date,
        total=total,
        paid_amount=Decimal("0"),
        status="open",
        created_by=identity.email or "",
    )
    db.add(purchase); db.flush()
    for line, item, line_total in locked_lines:
        purchase_line = PurchaseLine(purchase_id=purchase.id, item_id=item.id, quantity=line.quantity,
            unit_cost=line.unit_cost, line_total=line_total, previous_unit_cost=item.unit_cost)
        db.add(purchase_line); db.flush()
        item.quantity = Decimal(item.quantity) + line.quantity
        item.unit_cost = line.unit_cost
        db.add(InventoryMovement(
            item_id=item.id,
            purchase_line_id=purchase_line.id,
            quantity=line.quantity,
            movement_type="purchase",
            unit_cost=line.unit_cost,
            reason=f"Compra {purchase.folio}" + (f" · Factura {purchase.invoice_number}" if purchase.invoice_number else ""),
            created_by=identity.email or "",
            created_at=datetime.combine(data.purchase_date, datetime.min.time(), tzinfo=timezone.utc),
        ))
        _queue_low_stock_alert(db, background_tasks, item)
    if data.initial_payment:
        _record_supplier_payment(db, purchase, data.initial_payment, data.payment_account_id or "", data.purchase_date, data.payment_reference, identity.email or "")
    db.commit(); db.refresh(purchase)
    return _purchase_result(db, purchase)


@router.post("/purchases/{purchase_id}/payments", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def add_supplier_payment(purchase_id: str, data: SupplierPaymentInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    purchase = db.scalar(select(Purchase).where(Purchase.id == purchase_id).with_for_update())
    if purchase is None:
        raise HTTPException(404, "Compra no encontrada.")
    if db.scalar(select(PurchaseCorrection.id).where(PurchaseCorrection.purchase_id == purchase.id)):
        raise HTTPException(409, "La compra ya fue corregida y no admite nuevos pagos.")
    balance = Decimal(purchase.total) - Decimal(purchase.paid_amount)
    if data.amount > balance:
        raise HTTPException(409, "El pago excede el saldo pendiente de esta compra.")
    _record_supplier_payment(db, purchase, data.amount, data.account_id, data.paid_on, data.reference, identity.email or "")
    db.commit(); db.refresh(purchase)
    return _purchase_result(db, purchase)


@router.post("/purchases/{purchase_id}/payments/{payment_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def reverse_supplier_payment(
    purchase_id: str, payment_id: str, data: PaymentCorrectionInput,
    identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db),
):
    purchase = db.scalar(select(Purchase).where(Purchase.id == purchase_id).with_for_update())
    if purchase is None:
        raise HTTPException(404, "Compra no encontrada.")
    original = db.scalar(select(SupplierPayment).where(
        SupplierPayment.id == payment_id, SupplierPayment.purchase_id == purchase_id,
    ).with_for_update())
    if original is None:
        raise HTTPException(404, "Pago de proveedor no encontrado en esta compra.")
    if original.reversal_of_id is not None:
        raise HTTPException(409, "Una corrección no puede revertirse; registra un nuevo pago correcto si corresponde.")
    if db.scalar(select(SupplierPayment.id).where(SupplierPayment.reversal_of_id == original.id)):
        raise HTTPException(409, "Este pago ya tiene una corrección registrada.")
    if Decimal(purchase.paid_amount) < Decimal(original.amount):
        raise HTTPException(409, "El saldo pagado de la compra no coincide con el pago seleccionado; requiere conciliación.")
    cash_original = db.scalar(select(CashMovement).where(CashMovement.id == original.cash_movement_id).with_for_update())
    if cash_original is None:
        raise HTTPException(409, "El pago no tiene movimiento de caja/banco relacionado.")
    if db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == cash_original.id)):
        raise HTTPException(409, "El movimiento de caja ya fue revertido; requiere conciliación antes de corregir el pago.")
    cash_reversal = CashMovement(
        account_id=cash_original.account_id, direction="in" if cash_original.direction == "out" else "out",
        amount=cash_original.amount, category="Corrección de pago a proveedor",
        description=f"Reversa del pago {original.id} · {data.reason.strip()}", occurred_on=date.today(),
        source_type="supplier_payment_reversal", source_id=original.id, reversal_of_id=cash_original.id,
        created_by=identity.email or "",
    )
    db.add(cash_reversal); db.flush()
    correction = SupplierPayment(
        purchase_id=purchase.id, account_id=original.account_id, cash_movement_id=cash_reversal.id,
        amount=original.amount, paid_on=date.today(), reference=f"Corrección de pago {original.id}: {data.reason}",
        reversal_of_id=original.id, created_by=identity.email or "",
    )
    db.add(correction); db.flush(); cash_reversal.source_id = correction.id
    purchase.paid_amount = Decimal(purchase.paid_amount) - Decimal(original.amount)
    purchase.status = "paid" if purchase.paid_amount >= purchase.total else "partially_paid" if purchase.paid_amount > 0 else "open"
    db.commit(); db.refresh(purchase)
    return _purchase_result(db, purchase)


@router.post("/purchases/{purchase_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def reverse_purchase(
    purchase_id: str, data: PaymentCorrectionInput,
    identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db), background_tasks: BackgroundTasks = None,
):
    if not ({"administrador", "admin", "contador"} & set(identity.roles)):
        raise HTTPException(403, "Solo administración o contabilidad puede corregir una compra.")
    purchase = db.scalar(select(Purchase).where(Purchase.id == purchase_id).with_for_update())
    if purchase is None:
        raise HTTPException(404, "Compra no encontrada.")
    if db.scalar(select(PurchaseCorrection.id).where(PurchaseCorrection.purchase_id == purchase.id)):
        raise HTTPException(409, "Esta compra ya tiene una corrección registrada.")
    payments = db.scalars(select(SupplierPayment).where(SupplierPayment.purchase_id == purchase.id).with_for_update()).all()
    reversed_payment_ids = {payment.reversal_of_id for payment in payments if payment.reversal_of_id}
    if Decimal(purchase.paid_amount) != 0 or any(payment.reversal_of_id is None and payment.id not in reversed_payment_ids for payment in payments):
        raise HTTPException(409, "Revierte primero los pagos activos a proveedor desde el historial de la compra.")
    lines = db.scalars(select(PurchaseLine).where(PurchaseLine.purchase_id == purchase.id).order_by(PurchaseLine.item_id, PurchaseLine.id)).all()
    if not lines:
        raise HTTPException(409, "La compra no tiene renglones de inventario para corregir.")
    if len({line.item_id for line in lines}) != len(lines):
        raise HTTPException(409, "La compra tiene artículos repetidos; consolida sus renglones antes de corregirla.")

    receipts_by_line: dict[str, InventoryMovement] = {}
    items: dict[str, InventoryItem] = {}
    previous_cost_by_item: dict[str, Decimal] = {}
    for line in lines:
        if line.previous_unit_cost is None:
            raise HTTPException(409, "Esta compra es anterior al registro del costo previo; requiere conciliación manual antes de corregirla.")
        receipts = db.scalars(select(InventoryMovement).where(
            InventoryMovement.purchase_line_id == line.id,
            InventoryMovement.movement_type == "purchase",
        ).with_for_update()).all()
        if len(receipts) != 1:
            raise HTTPException(409, "Un renglón de compra no conserva exactamente una entrada de almacén; requiere conciliación.")
        receipt = receipts[0]
        receipts_by_line[line.id] = receipt
        previous_cost_by_item[line.item_id] = Decimal(line.previous_unit_cost)
        item = items.get(line.item_id)
        if item is None:
            item = db.scalar(select(InventoryItem).where(InventoryItem.id == line.item_id).with_for_update())
            if item is None:
                raise HTTPException(409, "Un artículo de la compra ya no existe en el catálogo.")
            items[line.item_id] = item
        if Decimal(item.quantity) < Decimal(line.quantity):
            raise HTTPException(409, f"No se puede revertir: el almacén ya no conserva {line.quantity} {item.unit} de {item.name}.")
        later_movement = db.scalar(select(InventoryMovement.id).where(
            InventoryMovement.item_id == item.id,
            InventoryMovement.id != receipt.id,
            InventoryMovement.created_at > receipt.created_at,
            InventoryMovement.reason != "existencia inicial",
        ).limit(1))
        later_purchase = db.scalar(select(InventoryMovement.id)
            .join(PurchaseLine, PurchaseLine.id == InventoryMovement.purchase_line_id)
            .join(Purchase, Purchase.id == PurchaseLine.purchase_id)
            .where(InventoryMovement.item_id == item.id, Purchase.id != purchase.id, Purchase.created_at > purchase.created_at)
            .limit(1))
        if later_movement or later_purchase:
            raise HTTPException(409, f"No se puede revertir: {items[line.item_id].name} tuvo movimientos de almacén posteriores a esta compra.")

    for line in lines:
        receipt = receipts_by_line[line.id]
        item = items[line.item_id]
        db.add(InventoryMovement(
            item_id=item.id, purchase_line_id=line.id, quantity=line.quantity,
            movement_type="purchase_reversal", unit_cost=line.unit_cost,
            related_movement_id=receipt.id,
            reason=f"Corrección de compra {purchase.folio}: {data.reason.strip()}",
            created_by=identity.email or "",
        ))
        item.quantity = Decimal(item.quantity) - Decimal(line.quantity)
        item.unit_cost = previous_cost_by_item[item.id]
        _queue_low_stock_alert(db, background_tasks, item)

    db.add(PurchaseCorrection(
        purchase_id=purchase.id, amount=purchase.total, reason=data.reason.strip(),
        created_by=identity.email or "",
    ))
    purchase.status = "corrected"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Esta compra ya tiene una corrección registrada.")
    db.refresh(purchase)
    return _purchase_result(db, purchase)


@router.post("/receivables", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def add_receivable(data: ReceivableInput, db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = Receivable(**data.model_dump(), status="overdue" if data.due_date < date.today() else "pending"); db.add(row); db.commit(); db.refresh(row)
    return _receivable_result(db, row)


@router.get("/receivables", dependencies=[Depends(require_permissions(auth_service, "receivables:read"))])
def list_receivables(db: Session = Depends(get_db)):
    rows = db.scalars(select(Receivable).where(_uncorrected_receivable_filter()).order_by(Receivable.due_date)).all()
    return [_receivable_result(db, row) for row in rows]


def _uncorrected_receivable_filter():
    corrected_ids = (select(Receivable.id).join(Sale, Sale.quote_id == Receivable.quote_id)
        .join(SaleCorrection, SaleCorrection.sale_id == Sale.id))
    return Receivable.id.not_in(corrected_ids)


def _receivable_result(db: Session, row: Receivable):
    balance = Decimal(row.amount) - Decimal(row.paid_amount)
    status = "paid" if balance <= 0 else "overdue" if row.due_date < date.today() else "partial" if row.paid_amount > 0 else "pending"
    payments = db.scalars(select(CustomerPayment).where(CustomerPayment.receivable_id == row.id).order_by(CustomerPayment.paid_on.desc(), CustomerPayment.created_at.desc())).all()
    account_names = {account.id: account.name for account in db.scalars(select(FinancialAccount).where(FinancialAccount.id.in_([payment.account_id for payment in payments]))).all()} if payments else {}
    reversed_payment_ids = {entry[0] for entry in db.execute(select(CustomerPayment.reversal_of_id).where(CustomerPayment.reversal_of_id.is_not(None))).all()}
    return {**_serialize(row), "customer": _serialize(db.get(Customer, row.customer_id)), "balance": balance, "status": status,
        "payments": [{**_serialize(payment), "account_name": account_names.get(payment.account_id, "Cuenta"),
            "is_reversal": payment.reversal_of_id is not None,
            "can_reverse": payment.reversal_of_id is None and payment.id not in reversed_payment_ids}
            for payment in payments]}


@router.post("/receivables/{receivable_id}/payments", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def record_payment(receivable_id: str, data: PaymentInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = db.scalar(select(Receivable).where(Receivable.id == receivable_id).with_for_update())
    if not row: raise HTTPException(404, "Cuenta por cobrar no encontrada.")
    if db.scalar(select(SaleCorrection.id).join(Sale, Sale.id == SaleCorrection.sale_id)
                 .where(Sale.quote_id == row.quote_id).limit(1)):
        raise HTTPException(409, "Esta venta fue corregida; no se pueden registrar cobros sobre sus cuotas canceladas.")
    balance = Decimal(row.amount) - Decimal(row.paid_amount)
    if data.amount > balance: raise HTTPException(409, "El pago excede el saldo pendiente.")
    account = db.scalar(select(FinancialAccount).where(FinancialAccount.id == data.account_id, FinancialAccount.active.is_(True)).with_for_update())
    if account is None: raise HTTPException(404, "Selecciona una cuenta de caja o banco activa para recibir el pago.")
    customer = db.get(Customer, row.customer_id)
    movement = CashMovement(account_id=account.id, direction="in", amount=data.amount,
        category="Cobranza de cliente", description=f"{customer.name if customer else 'Cliente'} · {row.payment_method}",
        occurred_on=data.paid_on, source_type="customer_payment", created_by=identity.email or "")
    db.add(movement); db.flush()
    payment = CustomerPayment(receivable_id=row.id, account_id=account.id, cash_movement_id=movement.id,
        amount=data.amount, paid_on=data.paid_on, reference=data.reference.strip(), created_by=identity.email or "")
    db.add(payment); db.flush(); movement.source_id = payment.id
    row.paid_amount = Decimal(row.paid_amount) + data.amount
    row.status = "paid" if row.paid_amount >= row.amount else "partial"
    db.commit(); db.refresh(row)
    return {**_receivable_result(db, row), "payment": _serialize(payment), "account_name": account.name}


@router.post("/receivables/{receivable_id}/payments/{payment_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def reverse_customer_payment(
    receivable_id: str, payment_id: str, data: PaymentCorrectionInput,
    identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db),
):
    receivable = db.scalar(select(Receivable).where(Receivable.id == receivable_id).with_for_update())
    if receivable is None:
        raise HTTPException(404, "Cuenta por cobrar no encontrada.")
    original = db.scalar(select(CustomerPayment).where(
        CustomerPayment.id == payment_id, CustomerPayment.receivable_id == receivable_id,
    ).with_for_update())
    if original is None:
        raise HTTPException(404, "Pago de cliente no encontrado en esta cuenta por cobrar.")
    if original.reversal_of_id is not None:
        raise HTTPException(409, "Una corrección no puede revertirse; registra un nuevo pago correcto si corresponde.")
    if db.scalar(select(CustomerPayment.id).where(CustomerPayment.reversal_of_id == original.id)):
        raise HTTPException(409, "Este pago ya tiene una corrección registrada.")
    if Decimal(receivable.paid_amount) < Decimal(original.amount):
        raise HTTPException(409, "El saldo pagado no coincide con el pago seleccionado; requiere conciliación.")
    cash_original = db.scalar(select(CashMovement).where(CashMovement.id == original.cash_movement_id).with_for_update())
    if cash_original is None:
        raise HTTPException(409, "El pago no tiene movimiento de caja/banco relacionado.")
    if db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == cash_original.id)):
        raise HTTPException(409, "El movimiento de caja ya fue revertido; requiere conciliación antes de corregir el pago.")
    customer = db.get(Customer, receivable.customer_id)
    cash_reversal = CashMovement(
        account_id=cash_original.account_id, direction="out" if cash_original.direction == "in" else "in",
        amount=cash_original.amount, category="Corrección de cobranza",
        description=f"Reversa del pago {original.id} · {data.reason.strip()}", occurred_on=date.today(),
        source_type="customer_payment_reversal", source_id=original.id, reversal_of_id=cash_original.id,
        created_by=identity.email or "",
    )
    db.add(cash_reversal); db.flush()
    correction = CustomerPayment(
        receivable_id=receivable.id, account_id=original.account_id, cash_movement_id=cash_reversal.id,
        amount=original.amount, paid_on=date.today(), reference=f"Corrección de pago {original.id}: {data.reason}",
        reversal_of_id=original.id, created_by=identity.email or "",
    )
    db.add(correction); db.flush(); cash_reversal.source_id = correction.id
    receivable.paid_amount = Decimal(receivable.paid_amount) - Decimal(original.amount)
    receivable.status = "paid" if receivable.paid_amount >= receivable.amount else "partial" if receivable.paid_amount > 0 else "overdue" if receivable.due_date < date.today() else "pending"
    db.commit(); db.refresh(receivable)
    return _receivable_result(db, receivable)


@router.get("/integrations", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def integration_status():
    drive = folder_status(settings)
    return {
        "google_drive": {
            **drive,
            "folder_configured": bool(settings.google_drive_folder_id),
            "service_account_configured": bool(getattr(settings, "google_drive_service_account_json", "")),
            "stored_file_types": ["quotes"],
            "planned_file_types": ["contracts", "receipts"],
        },
        "whatsapp": {
            "connected": False,
            "mode": "click_to_chat",
            "status": "click_to_chat_only",
            "business_phone_configured": bool(settings.whatsapp_phone),
        },
        "contract_signing": {"connected": False, "status": "provider_and_legal_review_required"},
        "electric_bill_analysis": {"connected": False, "status": "future_phase"},
    }


@router.get("/team", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def team_list(db: Session = Depends(get_db)):
    with auth_service.engine.connect() as connection:
        rows = connection.execute(select(users.c.id, users.c.email, users.c.name, memberships.c.roles, memberships.c.permissions).join(memberships, users.c.id == memberships.c.user_id).where(memberships.c.organization_id == settings.organization_id)).mappings().all()
    return [{"id": row["id"], "email": row["email"], "name": row["name"], "roles": sorted({canonical_role(role) for role in row["roles"]}), "permissions": row["permissions"]} for row in rows]


@router.get("/team/roles", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def team_roles():
    return [{"id": role, "label": label, "permissions": sorted(ROLE_PERMISSIONS[role])} for role, label in ROLE_LABELS.items()]


@router.post("/team", status_code=201, dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def team_create(data: TeamMemberInput):
    role = canonical_role(data.role)
    if role not in ROLE_PERMISSIONS: raise HTTPException(422, "Rol no permitido.")
    email = data.email.strip().lower()
    if role == "cliente":
        with SessionLocal() as db:
            if not db.scalar(select(Customer.id).where(func.lower(Customer.email) == email)):
                raise HTTPException(422, "Registra primero al cliente con este correo en la cartera.")
    identity = auth_service.create_user(email=email, name=data.name.strip(), password=data.password, organization_id=settings.organization_id, roles={role}, permissions=set(ROLE_PERMISSIONS[role]))
    return {"id": identity.user_id, "email": identity.email, "name": identity.name, "roles": sorted(identity.roles), "permissions": sorted(identity.permissions)}


@router.patch("/team/{user_id}", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def team_update_role(user_id: str, data: TeamRoleInput):
    role = canonical_role(data.role)
    if role not in ROLE_PERMISSIONS: raise HTTPException(422, "Rol no permitido.")
    with auth_service.engine.connect() as connection:
        member = connection.execute(select(memberships.c.user_id).where(memberships.c.user_id == user_id, memberships.c.organization_id == settings.organization_id)).first()
    if not member: raise HTTPException(404, "Usuario no encontrado.")
    if role == "cliente":
        with auth_service.engine.connect() as connection:
            email = connection.execute(select(users.c.email).where(users.c.id == user_id)).scalar_one_or_none()
        with SessionLocal() as db:
            if not email or not db.scalar(select(Customer.id).where(func.lower(Customer.email) == email.lower())):
                raise HTTPException(422, "Registra primero al cliente con este correo en la cartera.")
    auth_service.set_membership(user_id=user_id, organization_id=settings.organization_id, roles={role}, permissions=set(ROLE_PERMISSIONS[role]))
    return {"id": user_id, "roles": [role], "permissions": sorted(ROLE_PERMISSIONS[role])}


@router.get("/client/portal")
def client_portal(identity: AuthIdentity = Depends(require_permissions(auth_service, "client:portal")), db: Session = Depends(get_db)):
    return client_portal_data(identity, db)


def client_portal_data(identity: AuthIdentity, db: Session):
    if not identity.email:
        raise HTTPException(403, "La cuenta cliente necesita un correo asociado.")
    customers = db.scalars(select(Customer).where(func.lower(Customer.email) == identity.email.lower())).all()
    if not customers:
        raise HTTPException(404, "No hay una cuenta de cliente asociada a este correo.")
    customer_ids = [customer.id for customer in customers]
    quotes = db.scalars(select(Quote).where(Quote.customer_id.in_(customer_ids)).order_by(Quote.created_at.desc())).all()
    installations = db.scalars(select(Installation).where(Installation.customer_id.in_(customer_ids)).order_by(Installation.scheduled_at)).all()
    # Return a customer-facing projection. Never serialize internal cost fields,
    # customer links, installer emails, work notes or private Drive file IDs.
    return {
        "customers": [{"id": row.id, "name": row.name, "city": row.city, "status": row.status} for row in customers],
        "quotes": [{
            "id": row.id, "folio": row.folio, "panel_count": row.panel_count,
            "panel_brand": row.panel_brand, "panel_watts": row.panel_watts,
            "inverter": row.inverter, "total": row.total, "status": row.status,
            "created_at": row.created_at,
        } for row in quotes],
        "installations": [{
            "folio": row.folio, "scheduled_at": row.scheduled_at,
            "status": row.status,
            "checklist": [{"task": item.get("task", ""), "done": bool(item.get("done"))}
                          for item in (row.checklist or []) if isinstance(item, dict)],
        } for row in installations],
        "payments": [{"installment_number": row.installment_number, "due_date": row.due_date, "amount": row.amount, "paid_amount": row.paid_amount, "balance": float(row.amount) - float(row.paid_amount), "status": row.status, "payment_method": row.payment_method} for row in db.scalars(select(Receivable).where(Receivable.customer_id.in_(customer_ids), _uncorrected_receivable_filter()).order_by(Receivable.due_date)).all()],
    }


@router.get("/whatsapp-link", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def whatsapp_link(phone: str, message: str):
    digits = "".join(character for character in phone if character.isdigit())
    if len(digits) < 10: raise HTTPException(422, "El teléfono debe incluir al menos 10 dígitos.")
    return {"url": f"https://wa.me/{digits}?text={urlquote(message)}", "automatic_sending": False}


def _profitability_adjustment_result(row: ProfitabilityAdjustment, db: Session) -> dict:
    installation = db.get(Installation, row.installation_id) if row.installation_id else None
    customer = db.get(Customer, installation.customer_id) if installation else None
    reversed_by = db.scalar(select(ProfitabilityAdjustment.id).where(ProfitabilityAdjustment.reversal_of_id == row.id))
    return {
        **_serialize(row),
        "project": customer.name if customer else ("Sin proyecto" if row.installation_id is None else "Proyecto"),
        "folio": installation.folio if installation else None,
        "can_reverse": row.reversal_of_id is None and reversed_by is None,
    }


@router.get("/profitability-adjustments", dependencies=[Depends(require_permissions(auth_service, "reports:read"))])
def list_profitability_adjustments(
    month: str | None = None,
    installation_id: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(ProfitabilityAdjustment).order_by(ProfitabilityAdjustment.occurred_on.desc(), ProfitabilityAdjustment.created_at.desc())
    if month:
        try:
            year, month_number = (int(value) for value in month.split("-", maxsplit=1))
            start = date(year, month_number, 1)
            end = date(year + (month_number == 12), 1 if month_number == 12 else month_number + 1, 1)
        except (ValueError, TypeError):
            raise HTTPException(422, "El periodo debe tener formato AAAA-MM.")
        query = query.where(ProfitabilityAdjustment.occurred_on >= start, ProfitabilityAdjustment.occurred_on < end)
    if installation_id:
        query = query.where(ProfitabilityAdjustment.installation_id == installation_id)
    return [_profitability_adjustment_result(row, db) for row in db.scalars(query).all()]


@router.post("/profitability-adjustments", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:manage"))])
def create_profitability_adjustment(
    data: ProfitabilityAdjustmentInput,
    identity: AuthIdentity = Depends(identity_dependency(auth_service)),
    db: Session = Depends(get_db),
):
    if data.installation_id and db.get(Installation, data.installation_id) is None:
        raise HTTPException(404, "Proyecto u orden de trabajo no encontrado.")
    row = ProfitabilityAdjustment(
        installation_id=data.installation_id, adjustment_type=data.adjustment_type,
        description=data.description, amount=data.amount, occurred_on=data.occurred_on,
        created_by=identity.email or "",
    )
    db.add(row); db.commit(); db.refresh(row)
    return _profitability_adjustment_result(row, db)


@router.post("/profitability-adjustments/{adjustment_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:manage"))])
def reverse_profitability_adjustment(
    adjustment_id: str,
    data: PaymentCorrectionInput,
    identity: AuthIdentity = Depends(identity_dependency(auth_service)),
    db: Session = Depends(get_db),
):
    original = db.get(ProfitabilityAdjustment, adjustment_id)
    if original is None:
        raise HTTPException(404, "Devolución o bonificación no encontrada.")
    if original.reversal_of_id is not None or db.scalar(select(ProfitabilityAdjustment.id).where(ProfitabilityAdjustment.reversal_of_id == original.id)):
        raise HTTPException(409, "El registro ya fue corregido.")
    reversal = ProfitabilityAdjustment(
        installation_id=original.installation_id, adjustment_type=original.adjustment_type,
        description=f"Corrección: {data.reason}", amount=-Decimal(original.amount),
        occurred_on=date.today(), reversal_of_id=original.id, created_by=identity.email or "",
    )
    db.add(reversal); db.commit(); db.refresh(reversal)
    return _profitability_adjustment_result(reversal, db)


@router.get("/reports/profitability", dependencies=[Depends(require_permissions(auth_service, "reports:read"))])
def profitability_report(
    month: str | None = None,
    installation_id: str | None = None,
    project_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Show a preliminary operating result using recorded sales, material-use events, and expenses."""
    if month is not None:
        try:
            year_text, month_text = month.split("-", maxsplit=1)
            year, month_number = int(year_text), int(month_text)
            period_start = date(year, month_number, 1)
        except (ValueError, TypeError):
            raise HTTPException(422, "El periodo debe tener formato AAAA-MM.")
        if len(year_text) != 4 or len(month_text) != 2 or not 2000 <= year <= 2200:
            raise HTTPException(422, "El periodo debe tener formato AAAA-MM.")
        period_end = date(year + (month_number == 12), 1 if month_number == 12 else month_number + 1, 1)
        start_at = datetime.combine(period_start, datetime.min.time(), tzinfo=timezone.utc)
        end_at = datetime.combine(period_end, datetime.min.time(), tzinfo=timezone.utc)
    elif installation_id is None:
        today = date.today()
        period_start = date(today.year, today.month, 1)
        period_end = date(today.year + (today.month == 12), 1 if today.month == 12 else today.month + 1, 1)
        month = f"{today.year:04d}-{today.month:02d}"
        start_at = datetime.combine(period_start, datetime.min.time(), tzinfo=timezone.utc)
        end_at = datetime.combine(period_end, datetime.min.time(), tzinfo=timezone.utc)
    else:
        period_start = period_end = None
        start_at = end_at = None

    if installation_id and db.get(Installation, installation_id) is None:
        raise HTTPException(404, "Proyecto u orden de trabajo no encontrado.")
    if project_id and db.get(Project, project_id) is None:
        raise HTTPException(404, "Proyecto no encontrado.")

    grouped: dict[str | None, dict] = {}

    def project_row(key: str | None, installation: Installation | None = None) -> dict:
        project = db.get(Project, key) if key else None
        if project is None and installation and installation.project_id:
            project = db.get(Project, installation.project_id)
            key = installation.project_id
        if key not in grouped:
            customer = db.get(Customer, project.customer_id) if project else (db.get(Customer, installation.customer_id) if installation else None)
            grouped[key] = {
                "project_id": key,
                "installation_id": installation.id if installation else None,
                "folio": installation.folio if installation else None,
                "project_code": project.code if project else "",
                "project": project.name if project else (customer.name if customer else ("Gastos sin proyecto" if key is None else "Proyecto")),
                "city": customer.city if customer else "",
                "sales": Decimal("0"),
                "materials_cost": Decimal("0"),
                "expenses": Decimal("0"),
                "expenses_by_category": {},
                "expenses_by_type": {"fixed": Decimal("0"), "variable": Decimal("0"), "unclassified": Decimal("0")},
                "returns_and_bonifications": Decimal("0"),
                "adjustments_by_type": {"return": Decimal("0"), "bonification": Decimal("0")},
                "missing_cost_movements": 0,
                "material_events": 0,
            }
        row = grouped[key]
        if installation and row["installation_id"] is None:
            row["installation_id"] = installation.id
            row["folio"] = installation.folio
        return row

    sales_query = select(Sale, Installation, Customer).join(Installation, Installation.id == Sale.installation_id).join(Customer, Customer.id == Sale.customer_id)
    if installation_id:
        sales_query = sales_query.where(Sale.installation_id == installation_id)
    elif project_id:
        sales_query = sales_query.where(Installation.project_id == project_id)
    if start_at is not None and end_at is not None:
        sales_query = sales_query.where(Sale.created_at >= start_at, Sale.created_at < end_at)
    for sale, installation, customer in db.execute(sales_query).all():
        row = project_row(installation.project_id or installation.id, installation)
        row["project"] = db.get(Project, installation.project_id).name if installation.project_id else customer.name
        row["city"] = customer.city
        row["sales"] += Decimal(sale.total)

    corrections_query = select(SaleCorrection, Sale, Installation, Customer).join(
        Sale, Sale.id == SaleCorrection.sale_id,
    ).join(Installation, Installation.id == Sale.installation_id).join(Customer, Customer.id == Sale.customer_id)
    if installation_id:
        corrections_query = corrections_query.where(Sale.installation_id == installation_id)
    elif project_id:
        corrections_query = corrections_query.where(Installation.project_id == project_id)
    if start_at is not None and end_at is not None:
        corrections_query = corrections_query.where(SaleCorrection.created_at >= start_at, SaleCorrection.created_at < end_at)
    for correction, sale, installation, customer in db.execute(corrections_query).all():
        row = project_row(installation.project_id or installation.id, installation)
        row["project"] = db.get(Project, installation.project_id).name if installation.project_id else customer.name
        row["city"] = customer.city
        row["sales"] -= Decimal(correction.amount)

    material_query = select(InventoryMovement).where(InventoryMovement.movement_type.in_(["consumption", "consumption_return"]))
    if installation_id:
        material_query = material_query.where(InventoryMovement.installation_id == installation_id)
    elif project_id:
        material_query = material_query.join(Installation, Installation.id == InventoryMovement.installation_id).where(Installation.project_id == project_id)
    if start_at is not None and end_at is not None:
        material_query = material_query.where(InventoryMovement.created_at >= start_at, InventoryMovement.created_at < end_at)
    for movement in db.scalars(material_query).all():
        installation = db.get(Installation, movement.installation_id) if movement.installation_id else None
        row = project_row(installation.project_id if installation and installation.project_id else (installation.id if installation else None), installation)
        row["material_events"] += 1
        if movement.unit_cost is None:
            row["missing_cost_movements"] += 1
            continue
        quantity = Decimal(movement.quantity)
        cost = quantity * Decimal(movement.unit_cost)
        if movement.movement_type == "consumption_return":
            row["materials_cost"] -= cost
        else:
            row["materials_cost"] += cost

    expenses_query = select(ProjectExpense)
    if installation_id:
        expenses_query = expenses_query.where(ProjectExpense.installation_id == installation_id)
    elif project_id:
        expenses_query = expenses_query.where(ProjectExpense.project_id == project_id)
    if period_start is not None and period_end is not None:
        expenses_query = expenses_query.where(ProjectExpense.occurred_on >= period_start, ProjectExpense.occurred_on < period_end)
    for expense in db.scalars(expenses_query).all():
        installation = db.get(Installation, expense.installation_id) if expense.installation_id else None
        row = project_row(expense.project_id or ((installation.project_id or installation.id) if installation else None), installation)
        amount = Decimal(expense.amount)
        row["expenses"] += amount
        categories = row["expenses_by_category"]
        categories[expense.category] = categories.get(expense.category, Decimal("0")) + amount
        expense_type = expense.expense_type if expense.expense_type in {"fixed", "variable"} else "unclassified"
        row["expenses_by_type"][expense_type] += amount

    adjustments_query = select(ProfitabilityAdjustment)
    if installation_id:
        adjustments_query = adjustments_query.where(ProfitabilityAdjustment.installation_id == installation_id)
    elif project_id:
        adjustments_query = adjustments_query.join(Installation, Installation.id == ProfitabilityAdjustment.installation_id).where(Installation.project_id == project_id)
    if period_start is not None and period_end is not None:
        adjustments_query = adjustments_query.where(ProfitabilityAdjustment.occurred_on >= period_start, ProfitabilityAdjustment.occurred_on < period_end)
    adjustment_rows = db.scalars(adjustments_query).all()
    for adjustment in adjustment_rows:
        installation = db.get(Installation, adjustment.installation_id) if adjustment.installation_id else None
        row = project_row(installation.project_id if installation and installation.project_id else (installation.id if installation else None), installation)
        amount = Decimal(adjustment.amount)
        row["returns_and_bonifications"] += amount
        row["adjustments_by_type"][adjustment.adjustment_type] += amount

    rows = []
    for row in grouped.values():
        known_material_cost = row["materials_cost"] if row["missing_cost_movements"] == 0 else None
        rows.append({
            **row,
            "materials_cost": known_material_cost,
            "preliminary_result": row["sales"] - known_material_cost - row["expenses"] + row["returns_and_bonifications"] if known_material_cost is not None else None,
            "expenses_by_category": row["expenses_by_category"],
            "expenses_by_type": row["expenses_by_type"],
            "returns_and_bonifications": row["returns_and_bonifications"],
            "adjustments_by_type": row["adjustments_by_type"],
        })
    rows.sort(key=lambda row: (row["project"].casefold(), row["folio"] or ""))
    missing_costs = sum(row["missing_cost_movements"] for row in rows)
    sales_total = sum((row["sales"] for row in rows), Decimal("0"))
    expenses_total = sum((row["expenses"] for row in rows), Decimal("0"))
    expenses_by_type = {
        expense_type: sum((row["expenses_by_type"][expense_type] for row in rows), Decimal("0"))
        for expense_type in ("fixed", "variable", "unclassified")
    }
    adjustments_total = sum((row["returns_and_bonifications"] for row in rows), Decimal("0"))
    adjustments_by_type = {
        adjustment_type: sum((row["adjustments_by_type"][adjustment_type] for row in rows), Decimal("0"))
        for adjustment_type in ("return", "bonification")
    }
    material_cost_total = sum((row["materials_cost"] or Decimal("0") for row in rows), Decimal("0")) if missing_costs == 0 else None
    return {
        "period": month or (f"Proyecto · {project_id or installation_id}" if project_id or installation_id else "Todos los periodos"),
        "basis": "Ventas por fecha de registro; costo de materiales por fecha de consumo confirmado; gastos por fecha capturada.",
        "rows": rows,
        "totals": {
            "sales": sales_total,
            "materials_cost": material_cost_total,
            "expenses": expenses_total,
            "expenses_by_type": expenses_by_type,
            "returns_and_bonifications": adjustments_total,
            "adjustments_by_type": adjustments_by_type,
            "preliminary_result": sales_total - material_cost_total - expenses_total + adjustments_total if material_cost_total is not None else None,
            "missing_cost_movements": missing_costs,
        },
        "returns_and_bonifications": {"recorded": bool(adjustment_rows), "included": True, "total": adjustments_total},
        "complete_financial_statement": False,
    }


@router.get("/reports/operations")
def operations_report(
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 500,
    offset: int = 0,
    identity: AuthIdentity = Depends(require_permissions(auth_service, "reports:read")),
    db: Session = Depends(get_db),
):
    """Summarize current stock and recorded operational activity without inferred accounting rules."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "La fecha inicial debe ser anterior a la fecha final.")
    if limit < 1 or limit > 500 or offset < 0:
        raise HTTPException(422, "La página debe tener entre 1 y 500 movimientos y un desplazamiento no negativo.")
    start_at = datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc) if from_date else None
    end_at = datetime.combine(to_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc) if to_date else None

    reserved = {row[0]: Decimal(row[1] or 0) for row in db.execute(
        select(WorkOrderMaterial.item_id, func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity))
        .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
        .where(Installation.status.notin_(("closed", "cancelled")))
        .group_by(WorkOrderMaterial.item_id)
    ).all()}
    can_read_costs = bool({"inventory:costs:read", "inventory:manage"} & identity.permissions)
    stock_rows = []
    stock_value = Decimal("0")
    for item in db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all():
        held = reserved.get(item.id, Decimal("0"))
        available = max(Decimal(item.quantity) - held, Decimal("0"))
        stock_rows.append({
            "id": item.id, "name": item.name, "category": item.category, "unit": item.unit,
            "quantity": item.quantity, "reserved_quantity": held, "available_quantity": available,
            "minimum_quantity": item.minimum_quantity, "low_stock": item.minimum_quantity > 0 and available <= Decimal(item.minimum_quantity),
            **({"unit_cost": item.unit_cost} if can_read_costs else {}),
        })
        if can_read_costs:
            stock_value += Decimal(item.quantity) * Decimal(item.unit_cost or 0)

    movement_filters = []
    if start_at:
        movement_filters.append(InventoryMovement.created_at >= start_at)
    if end_at:
        movement_filters.append(InventoryMovement.created_at < end_at)
    movement_total = db.scalar(
        select(func.count(InventoryMovement.id)).where(*movement_filters)
    ) or 0
    movement_query = select(InventoryMovement, InventoryItem.name, InventoryItem.unit, Installation.folio).join(
        InventoryItem, InventoryItem.id == InventoryMovement.item_id
    ).outerjoin(Installation, Installation.id == InventoryMovement.installation_id)
    if movement_filters:
        movement_query = movement_query.where(*movement_filters)
    movement_rows = db.execute(
        movement_query.order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc())
        .limit(limit).offset(offset)
    ).all()
    has_more = offset + len(movement_rows) < movement_total
    inventory_movement_items = []
    movement_totals: dict[str, Decimal] = {}
    for movement, item_name, unit, folio in movement_rows:
        movement_totals[movement.movement_type] = movement_totals.get(movement.movement_type, Decimal("0")) + Decimal(movement.quantity)
        row = {
            "id": movement.id, "created_at": movement.created_at, "item_name": item_name,
            "unit": unit, "movement_type": movement.movement_type, "quantity": movement.quantity,
            "installation_folio": folio, "reason": movement.reason, "created_by": movement.created_by,
        }
        if can_read_costs:
            row["unit_cost"] = movement.unit_cost
        inventory_movement_items.append(row)

    def status_counts(rows):
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.status or "sin_estatus"] = counts.get(row.status or "sin_estatus", 0) + 1
        return [{"status": status, "count": count} for status, count in sorted(counts.items())]

    customers = db.scalars(select(Customer).order_by(Customer.created_at.desc(), Customer.id)).all()
    suppliers = db.scalars(select(Supplier).order_by(Supplier.name, Supplier.id)).all()
    installation_rows = db.execute(
        select(Installation, Customer.name, Customer.city)
        .outerjoin(Customer, Customer.id == Installation.customer_id)
        .order_by(Installation.scheduled_at.desc(), Installation.folio, Installation.id)
    ).all()
    installations = [row[0] for row in installation_rows]
    expense_filters = []
    if from_date:
        expense_filters.append(ProjectExpense.occurred_on >= from_date)
    if to_date:
        expense_filters.append(ProjectExpense.occurred_on <= to_date)
    expense_rows = db.execute(
        select(ProjectExpense, Installation.folio, Customer.name, Customer.city, FinancialAccount.name)
        .outerjoin(Installation, Installation.id == ProjectExpense.installation_id)
        .outerjoin(Customer, Customer.id == Installation.customer_id)
        .outerjoin(FinancialAccount, FinancialAccount.id == ProjectExpense.account_id)
        .where(*expense_filters)
        .order_by(ProjectExpense.occurred_on.desc(), ProjectExpense.created_at.desc(), ProjectExpense.id)
    ).all()
    expenses = [row[0] for row in expense_rows]
    expense_totals: dict[str, Decimal] = {}
    expense_type_totals = {"fixed": Decimal("0"), "variable": Decimal("0"), "unclassified": Decimal("0")}
    for expense in expenses:
        expense_totals[expense.category] = expense_totals.get(expense.category, Decimal("0")) + Decimal(expense.amount)
        expense_type = expense.expense_type if expense.expense_type in {"fixed", "variable"} else "unclassified"
        expense_type_totals[expense_type] += Decimal(expense.amount)

    cash_flow = None
    if "accounts:read" in identity.permissions:
        accounts = db.scalars(select(FinancialAccount).where(FinancialAccount.active.is_(True)).order_by(FinancialAccount.name)).all()
        account_ids = [account.id for account in accounts]
        cash_movements = db.scalars(select(CashMovement).where(CashMovement.account_id.in_(account_ids))).all() if account_ids else []
        account_rows = []
        total_opening = Decimal("0")
        total_opening_entries = Decimal("0")
        total_inflows = Decimal("0")
        total_outflows = Decimal("0")
        total_transfers_in = Decimal("0")
        total_transfers_out = Decimal("0")
        total_closing = Decimal("0")
        for account in accounts:
            seed = Decimal(account.opening_balance or 0)
            seed_date = account.opening_balance_date
            account_movements = [row for row in cash_movements if row.account_id == account.id and row.occurred_on >= seed_date]
            if from_date:
                if seed_date < from_date:
                    opening = seed + sum((Decimal(row.amount) if row.direction == "in" else -Decimal(row.amount)
                                          for row in account_movements if row.occurred_on < from_date), Decimal("0"))
                    opening_entry = Decimal("0")
                else:
                    opening = Decimal("0")
                    opening_entry = seed if seed_date <= (to_date or date.max) else Decimal("0")
                period_start = max(from_date, seed_date)
            elif to_date and seed_date > to_date:
                opening = Decimal("0")
                opening_entry = Decimal("0")
                period_start = seed_date
            else:
                opening = seed
                opening_entry = Decimal("0")
                period_start = seed_date
            in_period = [row for row in account_movements
                         if row.occurred_on >= period_start and (to_date is None or row.occurred_on <= to_date)]
            transfer_movements = [row for row in in_period if row.source_type in {"transfer", "transfer_reversal"}]
            transfers_in = sum((Decimal(row.amount) for row in transfer_movements if row.direction == "in"), Decimal("0"))
            transfers_out = sum((Decimal(row.amount) for row in transfer_movements if row.direction == "out"), Decimal("0"))
            inflows = sum((Decimal(row.amount) for row in in_period if row.direction == "in" and row.source_type not in {"transfer", "transfer_reversal"}), Decimal("0"))
            outflows = sum((Decimal(row.amount) for row in in_period if row.direction == "out" and row.source_type not in {"transfer", "transfer_reversal"}), Decimal("0"))
            closing = opening + opening_entry + inflows - outflows + transfers_in - transfers_out
            account_rows.append({
                "id": account.id, "name": account.name, "account_type": account.account_type,
                "opening_balance": opening, "opening_entries": opening_entry,
                "inflows": inflows, "outflows": outflows, "transfers_in": transfers_in,
                "transfers_out": transfers_out, "closing_balance": closing,
            })
            total_opening += opening
            total_opening_entries += opening_entry
            total_inflows += inflows
            total_outflows += outflows
            total_transfers_in += transfers_in
            total_transfers_out += transfers_out
            total_closing += closing
        cash_flow = {
            "from_date": from_date, "to_date": to_date,
            "opening_balance": total_opening, "opening_entries": total_opening_entries,
            "inflows": total_inflows, "outflows": total_outflows,
            "transfers_in": total_transfers_in, "transfers_out": total_transfers_out,
            "closing_balance": total_closing,
            "accounts": account_rows,
            "basis": "Cuentas activas; entradas y salidas excluyen transferencias internas, mostradas aparte. El saldo incluye ambos lados de cada transferencia por fecha capturada. No incluye proyecciones ni conciliación bancaria.",
        }

    return {
        "period": {"from_date": from_date, "to_date": to_date},
        "basis": "Existencia y reservas actuales; movimientos de almacén por fecha de registro; gastos por fecha capturada. Los totales no son una póliza contable.",
        "stock": {
            "items": stock_rows, "item_count": len(stock_rows),
            "low_stock_count": sum(1 for row in stock_rows if row["low_stock"]),
            "estimated_value": stock_value if can_read_costs else None,
        },
        "movements": {
            "items": inventory_movement_items, "total": movement_total, "offset": offset,
            "limit": limit, "has_more": has_more, "truncated": has_more,
            "totals_by_type": [{"movement_type": key, "quantity": quantity} for key, quantity in sorted(movement_totals.items())],
        },
        "customers_by_status": status_counts(customers),
        "suppliers": {"total": len(suppliers), "active": sum(1 for supplier in suppliers if supplier.active), "inactive": sum(1 for supplier in suppliers if not supplier.active)},
        "installations_by_status": status_counts(installations),
        "expenses": {"total": sum(expense_totals.values(), Decimal("0")), "by_category": [{"category": key, "amount": amount} for key, amount in sorted(expense_totals.items())], "by_type": expense_type_totals, "count": len(expenses)},
        "details": {
            "customers": [{
                "id": customer.id, "name": customer.name, "city": customer.city,
                "status": customer.status, "created_at": customer.created_at,
            } for customer in customers],
            "suppliers": [{
                "id": supplier.id, "name": supplier.name, "payment_terms": supplier.payment_terms,
                "credit_days": supplier.credit_days, "active": supplier.active, "created_at": supplier.created_at,
            } for supplier in suppliers],
            "installations": [{
                "id": installation.id, "folio": installation.folio, "customer": customer_name or "Cliente sin ficha",
                "city": customer_city or "", "scheduled_at": installation.scheduled_at,
                "status": installation.status,
            } for installation, customer_name, customer_city in installation_rows],
            "expenses": [{
                "id": expense.id, "occurred_on": expense.occurred_on, "category": expense.category,
                "expense_type": expense.expense_type,
                "description": expense.description, "amount": expense.amount,
                "project_folio": folio, "project_customer": customer_name or "Gasto operativo",
                "project_city": customer_city or "", "account": account_name or "Sin cuenta vinculada",
                "created_by": expense.created_by, "is_correction": expense.reversal_of_id is not None,
            } for expense, folio, customer_name, customer_city, account_name in expense_rows],
        },
        "cash_flow": cash_flow,
    }


@router.get("/dashboard")
def dashboard(identity: AuthIdentity = Depends(require_permissions(auth_service, "customers:read")), db: Session = Depends(get_db)):
    active_quotes = Quote.status.in_(["draft", "sent"])
    result = {
        "customers": db.scalar(select(func.count()).select_from(Customer)) or 0,
        "quotes_open": db.scalar(select(func.count()).select_from(Quote).where(active_quotes)) or 0,
        "quotes_amount": float(db.scalar(select(func.coalesce(func.sum(Quote.total), 0)).where(active_quotes)) or 0),
        "installations_active": db.scalar(select(func.count()).select_from(Installation).where(Installation.status.notin_(("closed", "cancelled")))) or 0,
        "receivables_open": 0.0,
        "due_receivables": [],
        "low_stock_items": [],
        "account_balances": [],
    }
    if "receivables:read" in identity.permissions:
        result["receivables_open"] = float(db.scalar(select(func.coalesce(func.sum(Receivable.amount-Receivable.paid_amount), 0)).where(Receivable.status != "paid", _uncorrected_receivable_filter())) or 0)
        due_rows = db.execute(select(Receivable, Customer.name).join(Customer, Customer.id == Receivable.customer_id)
            .where(Receivable.status != "paid", Receivable.due_date <= date.today() + timedelta(days=7), _uncorrected_receivable_filter())
            .order_by(Receivable.due_date).limit(10)).all()
        result["due_receivables"] = [{"id": row.id, "customer": name, "due_date": row.due_date, "balance": max(Decimal(row.amount) - Decimal(row.paid_amount), Decimal("0")), "status": "overdue" if row.due_date < date.today() else "due"} for row, name in due_rows]
    if "inventory:read" in identity.permissions:
        reserved = {item_id: Decimal(quantity or 0) for item_id, quantity in db.execute(
            select(WorkOrderMaterial.item_id, func.sum(WorkOrderMaterial.requested_quantity - WorkOrderMaterial.preissued_quantity))
            .join(Installation, Installation.id == WorkOrderMaterial.installation_id)
            .where(Installation.status.notin_(("closed", "cancelled"))).group_by(WorkOrderMaterial.item_id)
        ).all()}
        inventory_items = db.scalars(select(InventoryItem).where(InventoryItem.minimum_quantity > 0).order_by(InventoryItem.name)).all()
        result["low_stock_items"] = [{"id": item.id, "name": item.name, "unit": item.unit,
            "available_quantity": max(Decimal(item.quantity) - reserved.get(item.id, Decimal("0")), Decimal("0")),
            "minimum_quantity": Decimal(item.minimum_quantity)} for item in inventory_items
            if max(Decimal(item.quantity) - reserved.get(item.id, Decimal("0")), Decimal("0")) <= Decimal(item.minimum_quantity)][:10]
    if "accounts:read" in identity.permissions:
        accounts = db.scalars(select(FinancialAccount).where(FinancialAccount.active.is_(True)).order_by(FinancialAccount.name)).all()
        result["account_balances"] = [{"id": account.id, "name": account.name, "account_type": account.account_type,
            "balance": Decimal(account.opening_balance) + sum((Decimal(row.amount) if row.direction == "in" else -Decimal(row.amount) for row in db.scalars(select(CashMovement).where(CashMovement.account_id == account.id)).all()), Decimal("0"))} for account in accounts]
    return result
