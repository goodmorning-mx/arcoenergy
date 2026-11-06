from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO
from typing import Literal
from urllib.parse import quote as urlquote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select, text
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
from app.models import Activity, CashMovement, Customer, CustomerPayment, FinancialAccount, FollowUp, HistoryCard, Installation, InventoryItem, InventoryMovement, ProjectExpense, Purchase, PurchaseLine, Quote, QuotePackage, Receivable, Supplier, SupplierPayment
from app.roles import ROLE_LABELS, ROLE_PERMISSIONS, canonical_role

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


def get_db():
    with SessionLocal() as session:
        yield session


def _serialize(row):
    if row is None:
        return None
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


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


class NoteInput(BaseModel):
    note: str = Field(min_length=1, max_length=5000)
    kind: str = "nota"


class InstallationInput(BaseModel):
    customer_id: str
    quote_id: str | None = None
    scheduled_at: datetime | None = None
    lead_installer: str = ""
    notes: str = ""


class StockInput(BaseModel):
    item_id: str
    quantity: float = Field(gt=0)
    reason: str = "consumo en instalación"
    installation_id: str | None = None


class InventoryReturnInput(BaseModel):
    out_movement_id: str
    quantity: float = Field(gt=0)
    reason: str = "Devolución de material sobrante"


class StockReceiptInput(BaseModel):
    item_id: str
    quantity: float = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    reason: str = "entrada de almacén"


class InventoryItemInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    unit: str = Field(default="pieza", max_length=40)
    minimum_quantity: float = Field(default=0, ge=0)
    initial_quantity: float = Field(default=0, ge=0)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)


class ExpenseInput(BaseModel):
    installation_id: str | None = None
    account_id: str | None = None
    category: str = "Viáticos"
    description: str = Field(min_length=2, max_length=240)
    amount: Decimal = Field(gt=0)
    receipt_url: str = ""
    occurred_on: date = Field(default_factory=date.today)


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


class SupplierPaymentInput(BaseModel):
    amount: Decimal = Field(gt=0)
    account_id: str
    paid_on: date = Field(default_factory=date.today)
    reference: str = Field(default="", max_length=180)


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


class HistoryCardInput(BaseModel):
    story_id: str = Field(min_length=1, max_length=30)
    version: int = Field(ge=1)
    iteration: str = Field(min_length=1, max_length=80)
    stakeholder: str = Field(min_length=1, max_length=180)
    source_literal: str = Field(min_length=1)
    source_type: str = Field(min_length=1, max_length=40)
    source_reference: str = ""
    normalized_story: str = Field(min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    linked_cards: list[str] = Field(default_factory=list)


@router.get("/history-cards", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def list_history_cards(db: Session = Depends(get_db)):
    return [_serialize(row) for row in db.scalars(select(HistoryCard).order_by(HistoryCard.story_id, HistoryCard.version)).all()]


@router.post("/history-cards", status_code=201, dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def append_history_card(data: HistoryCardInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    latest = db.scalar(select(func.max(HistoryCard.version)).where(HistoryCard.story_id == data.story_id)) or 0
    if data.version != latest + 1:
        raise HTTPException(409, f"La siguiente versión disponible para {data.story_id} es {latest + 1}.")
    row = HistoryCard(**data.model_dump(), recorded_by=identity.email)
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
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{row.folio}.pdf"', "X-Drive-Status": "pending-configuration"})


@router.post("/followups", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def create_followup(data: FollowUpInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = FollowUp(**data.model_dump(), created_by=identity.email); db.add(row); db.flush()
    db.add(Activity(customer_id=row.customer_id, kind="seguimiento programado", note=f"{row.due_date}: {row.note}", created_by=identity.email)); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/followups", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def list_followups(db: Session = Depends(get_db)):
    rows = db.scalars(select(FollowUp).where(FollowUp.done.is_(False)).order_by(FollowUp.due_date)).all()
    return [{**_serialize(row), "customer": _serialize(db.get(Customer, row.customer_id))} for row in rows]


@router.patch("/followups/{followup_id}", dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def update_followup(followup_id: str, data: FollowUpDoneInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = db.get(FollowUp, followup_id)
    if row is None: raise HTTPException(404, "Seguimiento no encontrado.")
    row.done = data.done
    if data.done:
        db.add(Activity(customer_id=row.customer_id, kind="seguimiento completado", note=f"Seguimiento del {row.due_date}: {row.note}", created_by=identity.email))
    db.commit(); db.refresh(row)
    return _serialize(row)


@router.post("/installations", status_code=201, dependencies=[Depends(require_permissions(auth_service, "installations:write"))])
def create_installation(data: InstallationInput, db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    if data.lead_installer:
        with auth_service.engine.connect() as connection:
            member = connection.execute(select(users.c.id).join(memberships, memberships.c.user_id == users.c.id).where(users.c.email == data.lead_installer.lower(), users.c.is_active.is_(True), memberships.c.organization_id == settings.organization_id, memberships.c.roles.contains(["instalador"]))).first()
        if member is None:
            raise HTTPException(422, "Selecciona una cuenta activa con rol de instalador.")
    row = Installation(customer_id=data.customer_id, quote_id=data.quote_id, scheduled_at=data.scheduled_at, lead_installer=data.lead_installer, notes=data.notes, checklist=[{"task":"Confirmar materiales","done":False},{"task":"Asignar cuadrilla","done":False},{"task":"Visita de instalación","done":False},{"task":"Registrar consumos","done":False},{"task":"Cerrar proyecto","done":False}])
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/installations")
def list_installations(identity: AuthIdentity = Depends(require_permissions(auth_service, "installations:read")), db: Session = Depends(get_db)):
    query = select(Installation).order_by(Installation.scheduled_at)
    if "instalador" in identity.roles:
        query = query.where(Installation.lead_installer == identity.email)
    rows = db.scalars(query).all()
    return [{**_serialize(row), "customer": _serialize(db.get(Customer, row.customer_id))} for row in rows]


@router.get("/inventory")
def list_inventory(identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:read")), db: Session = Depends(get_db)):
    rows = [_serialize(row) for row in db.scalars(select(InventoryItem).order_by(InventoryItem.name)).all()]
    if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
        for row in rows:
            row.pop("unit_cost", None)
    return rows


@router.post("/inventory/items", status_code=201, dependencies=[Depends(require_permissions(auth_service, "inventory:manage"))])
def create_inventory_item(data: InventoryItemInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = InventoryItem(name=data.name.strip(), unit=data.unit.strip(), quantity=data.initial_quantity, minimum_quantity=data.minimum_quantity, unit_cost=data.unit_cost)
    db.add(row); db.flush()
    if data.initial_quantity:
        db.add(InventoryMovement(item_id=row.id, quantity=data.initial_quantity, movement_type="in", unit_cost=data.unit_cost, reason="existencia inicial", created_by=identity.email))
    db.commit(); db.refresh(row)
    return _serialize(row)


@router.post("/inventory/consume", status_code=201)
def consume_inventory(data: StockInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:write")), db: Session = Depends(get_db)):
    if "instalador" in identity.roles:
        installation = db.get(Installation, data.installation_id) if data.installation_id else None
        if installation is None or installation.lead_installer.lower() != (identity.email or "").lower():
            raise HTTPException(403, "Solo puedes registrar consumos en una orden asignada a tu cuenta.")
    item = db.get(InventoryItem, data.item_id)
    if not item: raise HTTPException(404, "Artículo no encontrado.")
    if float(item.quantity) < data.quantity: raise HTTPException(409, "Existencia insuficiente para este consumo.")
    item.quantity = float(item.quantity) - data.quantity
    movement = InventoryMovement(**data.model_dump(), movement_type="out", unit_cost=item.unit_cost, created_by=identity.email); db.add(movement); db.commit(); db.refresh(movement)
    serialized_item = _serialize(item)
    if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
        serialized_item.pop("unit_cost", None)
    return {"movement": _serialize(movement), "item": serialized_item}


@router.post("/inventory/receive", status_code=201)
def receive_inventory(data: StockReceiptInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:manage")), db: Session = Depends(get_db)):
    item = db.get(InventoryItem, data.item_id)
    if not item: raise HTTPException(404, "Artículo no encontrado.")
    item.quantity = float(item.quantity) + data.quantity
    item.unit_cost = data.unit_cost
    movement = InventoryMovement(item_id=data.item_id, quantity=data.quantity, movement_type="in", unit_cost=data.unit_cost, reason=data.reason, created_by=identity.email)
    db.add(movement); db.commit(); db.refresh(movement)
    return {"movement": _serialize(movement), "item": _serialize(item)}


@router.post("/inventory/returns", status_code=201)
def return_inventory(data: InventoryReturnInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:write")), db: Session = Depends(get_db)):
    source = db.scalar(select(InventoryMovement).where(InventoryMovement.id == data.out_movement_id).with_for_update())
    if source is None or source.movement_type != "out" or not source.installation_id:
        raise HTTPException(404, "No se encontró una salida de instalación válida para devolver.")
    if "instalador" in identity.roles:
        installation = db.get(Installation, source.installation_id)
        if installation is None or installation.lead_installer.lower() != (identity.email or "").lower():
            raise HTTPException(403, "Solo puedes devolver material de una orden asignada a tu cuenta.")
    returned = db.scalar(select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(
        InventoryMovement.related_movement_id == source.id,
        InventoryMovement.movement_type == "return",
    )) or 0
    if Decimal(str(returned)) + Decimal(str(data.quantity)) > Decimal(str(source.quantity)):
        raise HTTPException(409, "La cantidad devuelta excede el material retirado en esa salida.")
    item = db.get(InventoryItem, source.item_id)
    if item is None:
        raise HTTPException(409, "El artículo de la salida ya no existe en el catálogo.")
    item.quantity = Decimal(str(item.quantity)) + Decimal(str(data.quantity))
    movement = InventoryMovement(
        item_id=source.item_id,
        installation_id=source.installation_id,
        related_movement_id=source.id,
        quantity=data.quantity,
        movement_type="return",
        unit_cost=source.unit_cost,
        reason=data.reason.strip() or "Devolución de material sobrante",
        created_by=identity.email or "",
    )
    db.add(movement); db.commit(); db.refresh(movement)
    serialized_item = _serialize(item)
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
    identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:read")),
    db: Session = Depends(get_db),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(422, "La fecha inicial debe ser anterior a la fecha final.")
    return_rows = aliased(InventoryMovement)
    returned_total = select(func.coalesce(func.sum(return_rows.quantity), 0)).where(
        return_rows.related_movement_id == InventoryMovement.id,
        return_rows.movement_type == "return",
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
        query = query.join(Installation, Installation.id == InventoryMovement.installation_id).where(
            Installation.lead_installer == identity.email
        )
    query = query.order_by(InventoryMovement.created_at.desc()).limit(500)
    rows = db.execute(query).all()
    result = []
    for movement, item_name, unit, returned_quantity in rows:
        line = _serialize(movement)
        line.update({"item_name": item_name, "unit": unit, "signed_quantity": -float(movement.quantity) if movement.movement_type in {"out", "waste"} else float(movement.quantity)})
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
    if "instalador" in identity.roles and (installation is None or installation.lead_installer.lower() != (identity.email or "").lower()):
        raise HTTPException(403, "Selecciona una orden asignada a tu cuenta para registrar gastos de campo.")
    if "instalador" not in identity.roles and not data.account_id:
        raise HTTPException(422, "Selecciona la cuenta de caja o banco que pagó este gasto.")
    account = None
    if data.account_id:
        account = db.scalar(select(FinancialAccount).where(FinancialAccount.id == data.account_id, FinancialAccount.active.is_(True)).with_for_update())
        if account is None: raise HTTPException(404, "Selecciona una cuenta de caja o banco activa.")
    row = ProjectExpense(**data.model_dump(), created_by=identity.email); db.add(row); db.flush()
    if account:
        movement = CashMovement(account_id=account.id, direction="out", amount=data.amount,
            category=f"Gasto · {data.category}", description=data.description,
            occurred_on=data.occurred_on, source_type="expense", source_id=row.id,
            created_by=identity.email or "")
        db.add(movement)
    db.commit(); db.refresh(row)
    result = _serialize(row)
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
        installation = db.get(Installation, row.installation_id) if row.installation_id else None
        customer = db.get(Customer, installation.customer_id) if installation else None
        item["project_customer"] = customer.name if customer else "Gasto operativo"
        item["project_city"] = customer.city if customer else ""
        result.append(item)
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


@router.post("/cash-movements/{movement_id}/reverse", status_code=201, dependencies=[Depends(require_permissions(auth_service, "accounts:write"))])
def reverse_cash_movement(movement_id: str, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    original = db.scalar(select(CashMovement).where(CashMovement.id == movement_id).with_for_update())
    if original is None:
        raise HTTPException(404, "Movimiento de cuenta no encontrado.")
    if original.reversal_of_id is not None:
        raise HTTPException(409, "Una reversa no puede revertirse; registra un nuevo movimiento de corrección.")
    if db.scalar(select(CashMovement.id).where(CashMovement.reversal_of_id == movement_id)):
        raise HTTPException(409, "Este movimiento ya tiene una reversa registrada.")
    reversal = CashMovement(
        account_id=original.account_id,
        direction="out" if original.direction == "in" else "in",
        amount=original.amount,
        category="Corrección",
        description=f"Reversa del movimiento {original.id}: {original.description}",
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
    return [{**_serialize(row), "current_balance": Decimal(db.scalar(select(func.coalesce(func.sum(Purchase.total - Purchase.paid_amount), 0)).where(Purchase.supplier_id == row.id)) or 0)} for row in rows]


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
    return {
        **_serialize(purchase),
        "supplier": {"id": supplier.id, "name": supplier.name} if supplier else None,
        "balance": Decimal(purchase.total) - Decimal(purchase.paid_amount),
        "lines": [
            {**_serialize(line), "item_name": inventory_items.get(line.item_id, "Artículo")}
            for line in lines
        ],
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


@router.get("/purchases", dependencies=[Depends(require_permissions(auth_service, "purchases:read"))])
def list_purchases(db: Session = Depends(get_db)):
    return [_purchase_result(db, row) for row in db.scalars(select(Purchase).order_by(Purchase.purchase_date.desc(), Purchase.created_at.desc())).all()]


@router.post("/purchases", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def create_purchase(data: PurchaseInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
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
        purchase_line = PurchaseLine(purchase_id=purchase.id, item_id=item.id, quantity=line.quantity, unit_cost=line.unit_cost, line_total=line_total)
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
    if data.initial_payment:
        _record_supplier_payment(db, purchase, data.initial_payment, data.payment_account_id or "", data.purchase_date, data.payment_reference, identity.email or "")
    db.commit(); db.refresh(purchase)
    return _purchase_result(db, purchase)


@router.post("/purchases/{purchase_id}/payments", status_code=201, dependencies=[Depends(require_permissions(auth_service, "purchases:write"))])
def add_supplier_payment(purchase_id: str, data: SupplierPaymentInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    purchase = db.scalar(select(Purchase).where(Purchase.id == purchase_id).with_for_update())
    if purchase is None:
        raise HTTPException(404, "Compra no encontrada.")
    balance = Decimal(purchase.total) - Decimal(purchase.paid_amount)
    if data.amount > balance:
        raise HTTPException(409, "El pago excede el saldo pendiente de esta compra.")
    _record_supplier_payment(db, purchase, data.amount, data.account_id, data.paid_on, data.reference, identity.email or "")
    db.commit(); db.refresh(purchase)
    return _purchase_result(db, purchase)


@router.post("/receivables", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def add_receivable(data: ReceivableInput, db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = Receivable(**data.model_dump(), status="overdue" if data.due_date < date.today() else "pending"); db.add(row); db.commit(); db.refresh(row)
    return _receivable_result(db, row)


@router.get("/receivables", dependencies=[Depends(require_permissions(auth_service, "receivables:read"))])
def list_receivables(db: Session = Depends(get_db)):
    rows = db.scalars(select(Receivable).order_by(Receivable.due_date)).all()
    return [_receivable_result(db, row) for row in rows]


def _receivable_result(db: Session, row: Receivable):
    balance = Decimal(row.amount) - Decimal(row.paid_amount)
    status = "paid" if balance <= 0 else "overdue" if row.due_date < date.today() else "partial" if row.paid_amount > 0 else "pending"
    payments = db.scalars(select(CustomerPayment).where(CustomerPayment.receivable_id == row.id).order_by(CustomerPayment.paid_on.desc(), CustomerPayment.created_at.desc())).all()
    account_names = {account.id: account.name for account in db.scalars(select(FinancialAccount).where(FinancialAccount.id.in_([payment.account_id for payment in payments]))).all()} if payments else {}
    return {**_serialize(row), "customer": _serialize(db.get(Customer, row.customer_id)), "balance": balance, "status": status,
        "payments": [{**_serialize(payment), "account_name": account_names.get(payment.account_id, "Cuenta")} for payment in payments]}


@router.post("/receivables/{receivable_id}/payments", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def record_payment(receivable_id: str, data: PaymentInput, identity: AuthIdentity = Depends(identity_dependency(auth_service)), db: Session = Depends(get_db)):
    row = db.scalar(select(Receivable).where(Receivable.id == receivable_id).with_for_update())
    if not row: raise HTTPException(404, "Cuenta por cobrar no encontrada.")
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


@router.get("/integrations", dependencies=[Depends(require_permissions(auth_service, "team:manage"))])
def integration_status():
    drive = bool(settings.google_drive_folder_id)
    return {"google_drive": {"connected": drive, "status": "connected" if drive else "pending_configuration", "supports": ["quotes", "contracts", "receipts"]}, "whatsapp": {"connected": bool(settings.whatsapp_phone), "mode": "click_to_chat", "status": "configured" if settings.whatsapp_phone else "available_as_link"}, "contract_signing": {"connected": False, "status": "provider_and_legal_review_required"}, "electric_bill_analysis": {"connected": False, "status": "future_phase"}}


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
    return {
        "customers": [{"id": row.id, "name": row.name, "city": row.city, "status": row.status} for row in customers],
        "quotes": [_serialize(row) for row in db.scalars(select(Quote).where(Quote.customer_id.in_(customer_ids)).order_by(Quote.created_at.desc())).all()],
        "installations": [_serialize(row) for row in db.scalars(select(Installation).where(Installation.customer_id.in_(customer_ids)).order_by(Installation.scheduled_at)).all()],
        "payments": [{"installment_number": row.installment_number, "due_date": row.due_date, "amount": row.amount, "paid_amount": row.paid_amount, "balance": float(row.amount) - float(row.paid_amount), "status": row.status, "payment_method": row.payment_method} for row in db.scalars(select(Receivable).where(Receivable.customer_id.in_(customer_ids)).order_by(Receivable.due_date)).all()],
    }


@router.get("/whatsapp-link", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def whatsapp_link(phone: str, message: str):
    digits = "".join(character for character in phone if character.isdigit())
    if len(digits) < 10: raise HTTPException(422, "El teléfono debe incluir al menos 10 dígitos.")
    return {"url": f"https://wa.me/{digits}?text={urlquote(message)}", "automatic_sending": False}


@router.get("/dashboard", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def dashboard(db: Session = Depends(get_db)):
    active_quotes = Quote.status.in_(["draft", "sent"])
    return {"customers": db.scalar(select(func.count()).select_from(Customer)) or 0, "quotes_open": db.scalar(select(func.count()).select_from(Quote).where(active_quotes)) or 0, "quotes_amount": float(db.scalar(select(func.coalesce(func.sum(Quote.total), 0)).where(active_quotes)) or 0), "installations_active": db.scalar(select(func.count()).select_from(Installation).where(Installation.status != "closed")) or 0, "receivables_open": float(db.scalar(select(func.coalesce(func.sum(Receivable.amount-Receivable.paid_amount), 0)).where(Receivable.status != "paid")) or 0)}
