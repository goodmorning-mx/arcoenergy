from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from urllib.parse import quote as urlquote
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker
from gm_agent import AgentService, Conversation, Message, OpenAIProvider
from gm_mcp import Permission, RequestContext, ToolRegistry, tool
from openai import AsyncOpenAI
from gm_auth.dependencies import identity_dependency
from gm_auth.models import AuthIdentity
from gm_auth.models import memberships, users

from app.auth import auth_service
from app.config import get_settings
from app.database import create_database_engine
from app.models import Activity, Customer, FollowUp, Installation, InventoryItem, InventoryMovement, ProjectExpense, Quote, QuotePackage, Receivable
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
            description="Consulta los tamaños de sistema activos. Si hay precios aprobados, puede preparar una cotización estimada para el número de paneles solicitado y un inversor configurado. Nunca devuelve precios demo.",
            input_schema={"type": "object", "properties": {"panel_count": {"type": "integer", "minimum": 4, "maximum": 20}, "inverter": {"type": "string", "maxLength": 120}}, "additionalProperties": False},
            permission=Permission.READ,
        )
        def public_system_sizes(*, context: RequestContext, panel_count: int | None = None, inverter: str = ""):
            with SessionLocal() as db:
                rows = db.scalars(select(QuotePackage).where(QuotePackage.enabled.is_(True)).order_by(QuotePackage.panel_count)).all()
                result = {
                    "available_panel_counts": [row.panel_count for row in rows],
                    "pricing_approved": bool(rows) and all(not row.is_demo for row in rows),
                    "note": "No estimes ni inventes precios. Si el paquete elegido no está aprobado, pide los datos de contacto para que el equipo prepare la propuesta.",
                }
                if panel_count is None:
                    return result
                package = next((row for row in rows if row.panel_count == panel_count), None)
                if package is None:
                    return {**result, "quote": None, "note": "No hay un paquete activo para esa cantidad de paneles."}
                if package.is_demo:
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
                         "pricing_approved": not row.is_demo} for row in rows]

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
            "que la cotización solicitada no está aprobada o usa datos de demostración, dilo con claridad y ofrece que el equipo prepare "
            "una propuesta. No tienes permiso para crear ni modificar registros; solo puedes consultar datos permitidos."
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


class StockReceiptInput(BaseModel):
    item_id: str
    quantity: float = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    reason: str = "entrada de almacén"


class ExpenseInput(BaseModel):
    installation_id: str
    category: str = "Viáticos"
    description: str = ""
    amount: Decimal = Field(gt=0)
    receipt_url: str = ""


class ReceivableInput(BaseModel):
    customer_id: str
    due_date: date
    amount: Decimal = Field(gt=0)
    installment_number: int = Field(default=1, ge=1)
    quote_id: str | None = None
    payment_method: str = "Transferencia"


class PaymentInput(BaseModel):
    amount: Decimal = Field(gt=0)


class TeamMemberInput(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    email: str
    password: str = Field(min_length=12)
    role: str


class TeamRoleInput(BaseModel):
    role: str


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
            "catalog_status": "demo" if row.is_demo else "approved",
        })
    return {
        "demo": any(row.is_demo for row in rows),
        "packages": packages,
        "payment_methods": ["Contado", "Financiamiento", "Plan 24"],
        "catalog_note": "Los precios marcados como demostración son ilustrativos. Solo un administrador puede confirmar precios comerciales vigentes.",
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
    row.is_demo = not data.approved_prices
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
        is_demo=package.is_demo,
    )
    db.add(row); db.flush()
    mode = " (catálogo demo)" if package.is_demo else ""
    db.add(Activity(customer_id=customer.id, kind="cotización creada", note=f"Cotización {folio}{mode}, por ${total:,.2f} MXN.")); db.commit(); db.refresh(row)
    return {**_serialize(row), "demo_catalog": package.is_demo}


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
    if row.is_demo and data.status != "draft":
        raise HTTPException(409, "Aprueba el catálogo comercial antes de avanzar una cotización de demostración.")
    row.status = data.status
    db.add(Activity(customer_id=row.customer_id, kind="cotización actualizada", note=f"{row.folio}: {data.status}.", created_by=identity.email))
    db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/quotes/{quote_id}/pdf", dependencies=[Depends(require_permissions(auth_service, "quotes:read"))])
def quote_pdf(quote_id: str, db: Session = Depends(get_db)):
    row = db.get(Quote, quote_id)
    if not row: raise HTTPException(404, "Cotización no encontrada.")
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
    disclaimer = "DEMOSTRACIÓN — precios ilustrativos; no enviar como propuesta comercial." if row.is_demo else "Propuesta comercial sujeta a validación final de alcance y condiciones."
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


@router.post("/inventory/consume", status_code=201)
def consume_inventory(data: StockInput, identity: AuthIdentity = Depends(require_permissions(auth_service, "inventory:write")), db: Session = Depends(get_db)):
    item = db.get(InventoryItem, data.item_id)
    if not item: raise HTTPException(404, "Artículo no encontrado.")
    if float(item.quantity) < data.quantity: raise HTTPException(409, "Existencia insuficiente para este consumo.")
    item.quantity = float(item.quantity) - data.quantity
    movement = InventoryMovement(**data.model_dump()); db.add(movement); db.commit(); db.refresh(movement)
    serialized_item = _serialize(item)
    if not ({"inventory:costs:read", "inventory:manage"} & identity.permissions):
        serialized_item.pop("unit_cost", None)
    return {"movement": _serialize(movement), "item": serialized_item}


@router.post("/inventory/receive", status_code=201, dependencies=[Depends(require_permissions(auth_service, "inventory:manage"))])
def receive_inventory(data: StockReceiptInput, db: Session = Depends(get_db)):
    item = db.get(InventoryItem, data.item_id)
    if not item: raise HTTPException(404, "Artículo no encontrado.")
    item.quantity = float(item.quantity) + data.quantity
    item.unit_cost = data.unit_cost
    movement = InventoryMovement(item_id=data.item_id, quantity=data.quantity, reason=data.reason)
    db.add(movement); db.commit(); db.refresh(movement)
    return {"movement": _serialize(movement), "item": _serialize(item)}


@router.post("/expenses", status_code=201, dependencies=[Depends(require_permissions(auth_service, "expenses:write"))])
def add_expense(data: ExpenseInput, db: Session = Depends(get_db)):
    if not db.get(Installation, data.installation_id): raise HTTPException(404, "Instalación no encontrada.")
    row = ProjectExpense(**data.model_dump()); db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/expenses", dependencies=[Depends(require_permissions(auth_service, "expenses:read"))])
def list_expenses(db: Session = Depends(get_db)):
    return [_serialize(row) for row in db.scalars(select(ProjectExpense).order_by(ProjectExpense.created_at.desc())).all()]


@router.post("/receivables", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def add_receivable(data: ReceivableInput, db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = Receivable(**data.model_dump(), status="overdue" if data.due_date < date.today() else "pending"); db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/receivables", dependencies=[Depends(require_permissions(auth_service, "receivables:read"))])
def list_receivables(db: Session = Depends(get_db)):
    rows = db.scalars(select(Receivable).order_by(Receivable.due_date)).all()
    return [{**_serialize(row), "customer": _serialize(db.get(Customer,row.customer_id)), "balance": float(row.amount)-float(row.paid_amount)} for row in rows]


@router.post("/receivables/{receivable_id}/payments", status_code=201, dependencies=[Depends(require_permissions(auth_service, "receivables:write"))])
def record_payment(receivable_id: str, data: PaymentInput, db: Session = Depends(get_db)):
    row = db.get(Receivable, receivable_id)
    if not row: raise HTTPException(404, "Cuenta por cobrar no encontrada.")
    balance = Decimal(row.amount) - Decimal(row.paid_amount)
    if data.amount > balance: raise HTTPException(409, "El pago excede el saldo pendiente.")
    row.paid_amount = Decimal(row.paid_amount) + data.amount
    row.status = "paid" if row.paid_amount >= row.amount else "partial"
    db.commit(); db.refresh(row)
    return _serialize(row)


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
    return {"customers": db.scalar(select(func.count()).select_from(Customer)) or 0, "quotes_open": db.scalar(select(func.count()).select_from(Quote).where(active_quotes)) or 0, "quotes_amount": float(db.scalar(select(func.coalesce(func.sum(Quote.total), 0)).where(active_quotes)) or 0), "installations_active": db.scalar(select(func.count()).select_from(Installation).where(Installation.status != "closed")) or 0, "receivables_open": float(db.scalar(select(func.coalesce(func.sum(Receivable.amount-Receivable.paid_amount), 0)).where(Receivable.status != "paid")) or 0), "demo_data": True}
