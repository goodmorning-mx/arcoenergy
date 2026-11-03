from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from io import BytesIO
from urllib.parse import quote as urlquote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker
from gm_auth.dependencies import identity_dependency
from gm_auth.models import AuthIdentity
from gm_auth.models import memberships, users

from app.auth import auth_service
from app.config import get_settings
from app.database import create_database_engine
from app.models import Activity, Customer, FollowUp, Installation, InventoryItem, InventoryMovement, ProjectExpense, Quote, Receivable
from app.roles import ROLE_LABELS, ROLE_PERMISSIONS, canonical_role

settings = get_settings()
engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
router = APIRouter(prefix="/v1", tags=["arcoenergy"])


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
    panel_brand: str = "Jinko"
    panel_watts: int = Field(default=610, ge=100, le=1000)
    inverter: str = ""
    payment_method: str = "Contado"


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


@router.get("/catalog")
def catalog():
    packages = []
    for count in range(4, 21):
        kw = count * 610 / 1000
        inverter = "Growatt 3 kW" if kw <= 3.7 else "Growatt 5 kW" if kw <= 5.5 else "Huawei 6 kW" if kw <= 8 else "Huawei 10 kW"
        panel_total = count * 13250
        inverter_cost = 16800 if kw <= 3.7 else 22900 if kw <= 5.5 else 31900 if kw <= 8 else 44800
        packages.append({"panel_count": count, "panel_brand": "Jinko", "panel_watts": 610, "system_kw": round(kw, 2), "inverter": inverter, "structure": "Estructura de aluminio", "price_mxn": panel_total + inverter_cost + 14900})
    return {"demo": True, "packages": packages, "catalog_note": "Precios y equipos ilustrativos; confirmar el catálogo comercial antes de emitir propuestas a clientes."}


@router.get("/customers", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def list_customers(db: Session = Depends(get_db)):
    return [_serialize(row) for row in db.scalars(select(Customer).order_by(Customer.created_at.desc())).all()]


@router.post("/customers", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def create_customer(data: CustomerInput, db: Session = Depends(get_db)):
    row = Customer(**data.model_dump())
    db.add(row); db.commit(); db.refresh(row)
    db.add(Activity(customer_id=row.id, kind="cliente creado", note="Registro inicial del cliente.")); db.commit()
    return _serialize(row)


@router.get("/customers/{customer_id}/activity", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def customer_activity(customer_id: str, db: Session = Depends(get_db)):
    if not db.get(Customer, customer_id): raise HTTPException(404, "Cliente no encontrado.")
    rows = db.scalars(select(Activity).where(Activity.customer_id == customer_id).order_by(Activity.created_at.desc())).all()
    return [_serialize(row) for row in rows]


@router.post("/customers/{customer_id}/activity", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def add_customer_activity(customer_id: str, data: NoteInput, db: Session = Depends(get_db)):
    if not db.get(Customer, customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = Activity(customer_id=customer_id, kind=data.kind, note=data.note)
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.post("/quotes", status_code=201, dependencies=[Depends(require_permissions(auth_service, "quotes:write"))])
def create_quote(data: QuoteInput, db: Session = Depends(get_db)):
    customer = db.get(Customer, data.customer_id)
    if not customer: raise HTTPException(404, "Cliente no encontrado.")
    kw = data.panel_count * data.panel_watts / 1000
    expected_inverter = "Growatt 3 kW" if kw <= 3.7 else "Growatt 5 kW" if kw <= 5.5 else "Huawei 6 kW" if kw <= 8 else "Huawei 10 kW"
    inverter = data.inverter or expected_inverter
    inverter_cost = 16800 if kw <= 3.7 else 22900 if kw <= 5.5 else 31900 if kw <= 8 else 44800
    panel_subtotal = Decimal(data.panel_count * 13250)
    structure_cost = Decimal("14900")
    total = panel_subtotal + Decimal(inverter_cost) + structure_cost
    sequence = db.execute(text("SELECT nextval('ae_quote_folio_seq')")).scalar_one()
    folio = f"AE-{datetime.now(timezone.utc).year}-{sequence:05d}"
    row = Quote(folio=folio, customer_id=customer.id, panel_count=data.panel_count, panel_brand=data.panel_brand, panel_watts=data.panel_watts, inverter=inverter, payment_method=data.payment_method, panel_subtotal=panel_subtotal, structure_cost=structure_cost, inverter_cost=Decimal(inverter_cost), total=total)
    db.add(row); db.flush()
    db.add(Activity(customer_id=customer.id, kind="cotización creada", note=f"Cotización {folio} por ${total:,.2f} MXN.")); db.commit(); db.refresh(row)
    return {**_serialize(row), "demo_catalog": True}


@router.get("/quotes", dependencies=[Depends(require_permissions(auth_service, "quotes:read"))])
def list_quotes(db: Session = Depends(get_db)):
    rows = db.scalars(select(Quote).order_by(Quote.created_at.desc())).all()
    return [{**_serialize(row), "customer": _serialize(db.get(Customer, row.customer_id))} for row in rows]


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
    pdf.setFont("Helvetica", 10); pdf.drawString(48, 580, f"Instalación: {customer.city if customer else 'Por definir'}")
    pdf.drawString(48, 540, f"{row.panel_count} paneles {row.panel_brand} de {row.panel_watts} W")
    pdf.drawString(48, 520, f"Inversor: {row.inverter}")
    pdf.drawString(48, 500, "Incluye estructura y propuesta de instalación.")
    pdf.line(48, 465, 564, 465)
    pdf.setFont("Helvetica", 11); pdf.drawString(48, 435, "Paneles"); pdf.drawRightString(564, 435, f"${float(row.panel_subtotal):,.2f} MXN")
    pdf.drawString(48, 412, "Estructura"); pdf.drawRightString(564, 412, f"${float(row.structure_cost):,.2f} MXN")
    pdf.drawString(48, 389, "Inversor"); pdf.drawRightString(564, 389, f"${float(row.inverter_cost):,.2f} MXN")
    pdf.setFont("Helvetica-Bold", 15); pdf.drawString(48, 345, "Inversión estimada")
    pdf.drawRightString(564, 345, f"${float(row.total):,.2f} MXN")
    pdf.setFont("Helvetica", 8); pdf.setFillColorRGB(.4, .45, .42); pdf.drawString(48, 65, "Propuesta de demostración. Precios y configuración comercial pendientes de validar.")
    pdf.save(); buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{row.folio}.pdf"', "X-Drive-Status": "pending-configuration"})


@router.post("/followups", status_code=201, dependencies=[Depends(require_permissions(auth_service, "customers:write"))])
def create_followup(data: FollowUpInput, db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = FollowUp(**data.model_dump()); db.add(row); db.flush()
    db.add(Activity(customer_id=row.customer_id, kind="seguimiento programado", note=f"{row.due_date}: {row.note}")); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/followups", dependencies=[Depends(require_permissions(auth_service, "customers:read"))])
def list_followups(db: Session = Depends(get_db)):
    rows = db.scalars(select(FollowUp).where(FollowUp.done.is_(False)).order_by(FollowUp.due_date)).all()
    return [_serialize(row) for row in rows]


@router.post("/installations", status_code=201, dependencies=[Depends(require_permissions(auth_service, "installations:write"))])
def create_installation(data: InstallationInput, db: Session = Depends(get_db)):
    if not db.get(Customer, data.customer_id): raise HTTPException(404, "Cliente no encontrado.")
    row = Installation(customer_id=data.customer_id, quote_id=data.quote_id, scheduled_at=data.scheduled_at, lead_installer=data.lead_installer, notes=data.notes, checklist=[{"task":"Confirmar materiales","done":False},{"task":"Asignar cuadrilla","done":False},{"task":"Visita de instalación","done":False},{"task":"Registrar consumos","done":False},{"task":"Cerrar proyecto","done":False}])
    db.add(row); db.commit(); db.refresh(row)
    return _serialize(row)


@router.get("/installations", dependencies=[Depends(require_permissions(auth_service, "installations:read"))])
def list_installations(db: Session = Depends(get_db)):
    rows = db.scalars(select(Installation).order_by(Installation.scheduled_at)).all()
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
    return {"customers": db.scalar(select(func.count()).select_from(Customer)) or 0, "quotes_open": db.scalar(select(func.count()).select_from(Quote).where(Quote.status == "sent")) or 0, "quotes_amount": float(db.scalar(select(func.coalesce(func.sum(Quote.total), 0)).where(Quote.status == "sent")) or 0), "installations_active": db.scalar(select(func.count()).select_from(Installation).where(Installation.status != "closed")) or 0, "receivables_open": float(db.scalar(select(func.coalesce(func.sum(Receivable.amount-Receivable.paid_amount), 0)).where(Receivable.status != "paid")) or 0), "demo_data": True}
