"""Repeatable, DEV-only ArcoEnergy demo data for product previews.

Run with ``python -m app.seed_dev_mock_data --apply`` inside the API container.
Rows use stable IDs and DEMO folios/names so reruns update only this fixture set.
Never seeds authentication, agent, notification, backup, or stakeholder evidence.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import create_database_engine
from app.models import (
    AccountingAccount, AccountingEntry, AccountingLine, Activity, CashMovement,
    Customer, CustomerPayment, FollowUp, FinancialAccount, Installation,
    InstallationAssignment, InventoryCategory, InventoryImportBatch,
    InventoryItem, InventoryMovement, Project, ProjectExpense,
    ProfitabilityAdjustment, Purchase, PurchaseLine, Quote, QuotePackage,
    Receivable, Sale, Supplier, SupplierPayment, WorkOrderMaterial,
)

DEMO_USER = "demo@arcoenergy.test"
DEMO_PREFIX = "arcoenergy-dev-preview-v1:"


def _id(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, DEMO_PREFIX + key))


def _put(db: Session, model_cls, key: str, **values):
    row_id = _id(key)
    row = db.get(model_cls, row_id)
    if row is None:
        row = model_cls(id=row_id)
        db.add(row)
    for name, value in values.items():
        setattr(row, name, value)
    db.flush()
    return row


def seed(db: Session, today: date | None = None) -> dict[str, int]:
    today = today or date.today()
    now = datetime.combine(today, time(12), tzinfo=timezone.utc)
    counts: dict[str, int] = {}

    def put(model_cls, key, **values):
        counts[model_cls.__name__] = counts.get(model_cls.__name__, 0) + 1
        return _put(db, model_cls, key, **values)

    # Customers, quote catalog, commercial pipeline and follow-up activity.
    customer_specs = [
        ("mariana", "DEMO · Mariana López", "833 555 0101", "mariana.demo@example.test", "Tampico", "Av. Hidalgo 120, Tampico, Tamps.", "customer", "web"),
        ("roberto", "DEMO · Roberto Salinas", "833 555 0102", "roberto.demo@example.test", "Ciudad Madero", "Calle Cedro 48, Ciudad Madero, Tamps.", "customer", "whatsapp"),
        ("paola", "DEMO · Paola Méndez", "833 555 0103", "paola.demo@example.test", "Altamira", "Privada del Sol 18, Altamira, Tamps.", "lead", "referral"),
        ("ernesto", "DEMO · Ernesto Castillo", "833 555 0104", "ernesto.demo@example.test", "Tampico", "Col. Petrolera, Tampico, Tamps.", "customer", "crm"),
        ("lucia", "DEMO · Lucía Torres", "833 555 0105", "lucia.demo@example.test", "Pueblo Viejo", "Centro, Pueblo Viejo, Ver.", "lead", "web"),
        ("fernando", "DEMO · Fernando Ríos", "833 555 0106", "fernando.demo@example.test", "Tampico", "Col. Águila, Tampico, Tamps.", "customer", "referral"),
    ]
    customers = {}
    for key, name, phone, email, city, address, status, source in customer_specs:
        customers[key] = put(Customer, f"customer-{key}", name=name, phone=phone, email=email, city=city,
                             address=address, status=status, source=source, created_at=now-timedelta(days=45))

    inverter = [{"brand": "Growatt", "model": "MIN 5000TL-X", "capacity_kw": 5},
                {"brand": "Growatt", "model": "MIN 6000TL-X", "capacity_kw": 6}]
    for panels in (4, 8, 12, 16, 20):
        existing = db.scalar(select(QuotePackage).where(QuotePackage.panel_count == panels))
        if existing is None:
            put(QuotePackage, f"package-{panels}", panel_count=panels, panel_brand="Jinko DEMO", panel_watts=610,
                panel_unit_price=Decimal("2840.00"), structure_name="Estructura residencial", structure_price=Decimal("6200.00"),
                inverter_options=inverter, default_inverter="Growatt MIN 5000TL-X" if panels <= 12 else "Growatt MIN 6000TL-X",
                payment_methods=["Contado", "Transferencia", "Financiamiento", "Plan 12 meses"], enabled=True,
                pricing_approved=True, updated_by=DEMO_USER, updated_at=now)

    quote_specs = [
        ("quote-mariana", "DEMO-COT-2026-001", "mariana", 8, "accepted", "Transferencia", 22600),
        ("quote-roberto", "DEMO-COT-2026-002", "roberto", 12, "accepted", "Financiamiento", 38900),
        ("quote-paola", "DEMO-COT-2026-003", "paola", 16, "sent", "Contado", 46800),
        ("quote-ernesto", "DEMO-COT-2026-004", "ernesto", 20, "draft", "Contado", 61900),
        ("quote-lucia", "DEMO-COT-2026-005", "lucia", 8, "sent", "Financiamiento", 22600),
        ("quote-fernando", "DEMO-COT-2026-006", "fernando", 16, "accepted", "Financiamiento", 46800),
    ]
    quotes = {}
    for key, folio, cust, panels, status, method, inverter_cost in quote_specs:
        panel_subtotal = Decimal(panels * 2840)
        structure_cost = Decimal("6200.00")
        quotes[key] = put(Quote, key, folio=folio, customer_id=customers[cust].id,
            installation_address=customers[cust].address, installation_city=customers[cust].city,
            panel_count=panels, panel_brand="Jinko DEMO", panel_watts=610,
            structure_name="Estructura residencial", inverter="Growatt MIN 5000TL-X" if panels <= 12 else "Growatt MIN 6000TL-X",
            payment_method=method, panel_subtotal=panel_subtotal, structure_cost=structure_cost,
            inverter_cost=Decimal(inverter_cost), total=panel_subtotal+structure_cost+Decimal(inverter_cost),
            status=status, pricing_approved=True, drive_file_id="", created_at=now-timedelta(days=14 if status=="accepted" else 2))

    for cust, quote_key, due, note, done, assigned in [
        ("paola", "quote-paola", 3, "DEMO · Confirmar recepción de propuesta y resolver dudas de ahorro.", False, "elder.gonzalez@arcoenergy.mx"),
        ("lucia", "quote-lucia", -2, "DEMO · Seguimiento vencido: validar opción de financiamiento.", False, "elder.gonzalez@arcoenergy.mx"),
        ("mariana", "quote-mariana", -1, "DEMO · Seguimiento completado después de confirmar transferencia.", True, "josue.agundiz@arcoenergy.mx"),
    ]:
        put(FollowUp, f"followup-{cust}", customer_id=customers[cust].id, quote_id=quotes[quote_key].id,
            due_date=today+timedelta(days=due), note=note, created_by=DEMO_USER, assigned_to=assigned,
            done=done, agent_intent_id=None, push_claimed_at=None, push_notified_at=None, created_at=now-timedelta(days=4))
    for cust, kind, note, days in [
        ("paola", "quote_sent", "DEMO · Cotización compartida por WhatsApp; pidió revisar alternativas.", 2),
        ("mariana", "sale_created", "DEMO · Aceptó la propuesta y confirmó fecha de instalación.", 8),
        ("roberto", "payment_received", "DEMO · Se registró el anticipo del plan financiado.", 1),
    ]:
        put(Activity, f"activity-{cust}-{kind}", customer_id=customers[cust].id, kind=kind, note=note,
            created_by=DEMO_USER, created_at=now-timedelta(days=days))

    # Field teams, projects, work orders and installation lifecycle examples.
    project_specs = [
        ("mariana", "DEMO-PR-001", "Sistema residencial · Tampico", "in_progress", "high", 68, 8),
        ("roberto", "DEMO-PR-002", "Sistema residencial · Ciudad Madero", "planning", "medium", 22, 18),
        ("fernando", "DEMO-PR-003", "Sistema residencial · Colonia Águila", "completed", "low", 100, -6),
        ("ernesto", "DEMO-PR-004", "Sistema comercial · Tampico", "on_hold", "medium", 35, 25),
    ]
    projects = {}
    for cust, code, name, status, priority, progress, due in project_specs:
        quote = quotes[{"mariana":"quote-mariana", "roberto":"quote-roberto", "fernando":"quote-fernando", "ernesto":"quote-ernesto"}[cust]]
        projects[cust] = put(Project, f"project-{cust}", code=code, customer_id=customers[cust].id,
            name=name, notes="DEMO · Datos ficticios para previsualización del flujo operativo y financiero.",
            location=customers[cust].address, status=status, source_status=status, priority=priority,
            progress_percent=Decimal(progress), due_date=today+timedelta(days=due), contract_amount=quote.total,
            source="crm", created_by=DEMO_USER, created_at=now-timedelta(days=12))

    install_specs = [
        ("mariana", "DEMO-OT-001", "in_progress", -1, ["Levantamiento", "Montaje", "Pruebas", "Entrega"]),
        ("roberto", "DEMO-OT-002", "assigned", 4, ["Confirmar acceso", "Montaje", "Pruebas"]),
        ("fernando", "DEMO-OT-003", "closed", -8, ["Levantamiento", "Montaje", "Pruebas", "Entrega"]),
    ]
    installs = {}
    for cust, folio, status, offset, checklist in install_specs:
        qkey = {"mariana":"quote-mariana", "roberto":"quote-roberto", "fernando":"quote-fernando"}[cust]
        installs[cust] = put(Installation, f"installation-{cust}", folio=folio, customer_id=customers[cust].id,
            project_id=projects[cust].id, quote_id=quotes[qkey].id, scheduled_at=now+timedelta(days=offset),
            lead_installer="cesar.flores@arcoenergy.mx", status=status,
            checklist=[{"label": item, "done": item in checklist[:2] if status=="in_progress" else status=="closed"} for item in checklist],
            notes="DEMO · Orden de trabajo de muestra.", material_request_drive_file_id="",
            material_request_filename="", material_request_content_type="", material_request_updated_at=None)
        for email in ("cesar.flores@arcoenergy.mx", "instalador.demo@arcoenergy.test"):
            put(InstallationAssignment, f"assignment-{cust}-{email}", installation_id=installs[cust].id,
                installer_email=email, assigned_by="josue.agundiz@arcoenergy.mx",
                confirmed_at=now-timedelta(days=1) if email.startswith("cesar") and status=="in_progress" else None,
                created_at=now-timedelta(days=3))

    # Additional repeatable field-board examples bring DEV to ten installation cards.
    # These stay clearly labeled as DEMO and never overwrite non-demo installations.
    extra_install_specs = [
        ("004", "mariana", "assigned", 2),
        ("005", "roberto", "assigned", 5),
        ("006", "fernando", "in_progress", 1),
        ("007", "lucia", "in_progress", 9),
        ("008", "ernesto", "closed", -18),
        ("009", "paola", "closed", -26),
        ("010", "mariana", "assigned", 16),
    ]
    for suffix, cust, status, offset in extra_install_specs:
        installation = put(Installation, f"installation-demo-{suffix}",
            folio=f"DEMO-OT-{suffix}", customer_id=customers[cust].id,
            project_id=projects[cust].id if cust in projects else None,
            quote_id=quotes[f"quote-{cust}"].id, scheduled_at=now+timedelta(days=offset),
            lead_installer="cesar.flores@arcoenergy.mx", status=status,
            checklist=[{"label": task, "done": status == "closed" or (status == "in_progress" and index == 0)}
                       for index, task in enumerate(["Confirmar materiales", "Montaje", "Pruebas", "Entrega"])],
            notes="DEMO · Orden de trabajo ficticia para previsualizar el tablero.",
            material_request_drive_file_id="", material_request_filename="",
            material_request_content_type="", material_request_updated_at=None)
        for email in ("cesar.flores@arcoenergy.mx", "instalador.demo@arcoenergy.test"):
            put(InstallationAssignment, f"assignment-demo-{suffix}-{email}",
                installation_id=installation.id, installer_email=email,
                assigned_by="josue.agundiz@arcoenergy.mx",
                confirmed_at=now-timedelta(days=1) if email.startswith("cesar") and status == "in_progress" else None,
                created_at=now-timedelta(days=3))

    # Suppliers and product catalog. Existing real inventory and package prices remain untouched.
    suppliers = {}
    for key, name, contact, phone, terms, days in [
        ("solar", "DEMO · Solar del Golfo", "Andrea Fuentes", "833 555 0201", "credit", 30),
        ("electrico", "DEMO · Suministros Eléctricos Tamaulipas", "Luis García", "833 555 0202", "cash", 0),
    ]:
        suppliers[key] = put(Supplier, f"supplier-{key}", name=name, contact_name=contact,
            rfc="XAXX010101000", phone=phone, email=f"{key}.demo@example.test", payment_terms=terms,
            credit_days=days, active=True, created_by=DEMO_USER, created_at=now-timedelta(days=60))

    categories = {}
    for key, name, description in [
        ("modules", "Módulos fotovoltaicos", "DEMO · Paneles solares y módulos."),
        ("inverters", "Equipos de generación", "DEMO · Inversores y protecciones."),
        ("structure", "Estructura", "DEMO · Rieles, clamps y fijaciones."),
        ("electrical", "Material eléctrico", "DEMO · Conductores, conectores y tubería."),
    ]:
        categories[key] = put(InventoryCategory, f"category-{key}", name=name,
            name_key=name.casefold().replace(" ", "-"), description=description, active=True,
            created_by=DEMO_USER, created_at=now-timedelta(days=50))

    item_specs = [
        ("panel", "Panel solar monocristalino 610 W", "modules", "Paneles", "Jinko DEMO", "JKM610N-78HL4", 34, 5, 2860, "pza", "solar"),
        ("inv5", "Inversor Growatt 5 kW", "inverters", "Inversores", "Growatt DEMO", "MIN-5000TL-X", 4, 1, 18800, "pza", "solar"),
        ("inv6", "Inversor Growatt 6 kW", "inverters", "Inversores", "Growatt DEMO", "MIN-6000TL-X", 2, 1, 21200, "pza", "solar"),
        ("rail", "Riel aluminio 4.4 m", "structure", "Rieles", "K2 DEMO", "CR-44", 58, 12, 510, "pza", "solar"),
        ("lfoot", "L-Foot para teja", "structure", "Fijación", "K2 DEMO", "LFT-01", 96, 20, 49, "pza", "solar"),
        ("clamp", "Mid clamp aluminio", "structure", "Fijación", "K2 DEMO", "MC-35", 110, 24, 36, "pza", "solar"),
        ("endclamp", "End clamp aluminio", "structure", "Fijación", "K2 DEMO", "EC-35", 76, 20, 39, "pza", "solar"),
        ("connector", "Conector MC4 par", "electrical", "Conectores", "Stäubli DEMO", "MC4-EVO2", 42, 10, 94, "par", "electrico"),
        ("cablepv", "Cable fotovoltaico 6 mm²", "electrical", "Conductores", "Condumex DEMO", "PV-6-ROJO", 420, 100, 28, "m", "electrico"),
        ("tuberia", "Tubería PVC conduit 3/4 pulg.", "electrical", "Tubería", "Durman DEMO", "PVC-19", 65, 15, 32, "pza", "electrico"),
        ("breaker", "Interruptor termomagnético 2P 40 A", "electrical", "Protección", "Schneider DEMO", "C40-2P", 9, 3, 520, "pza", "electrico"),
        ("sealant", "Sellador Sikaflex exterior", "structure", "Selladores", "Sika DEMO", "SFK-300", 18, 6, 148, "pza", "electrico"),
    ]
    items = {}
    for key, name, cat, sub, brand, model_name, quantity, minimum, cost, unit, supplier_key in item_specs:
        items[key] = put(InventoryItem, f"item-{key}", code=f"DEMO-{key.upper()}", name=f"DEMO · {name}",
            description="Artículo ficticio para mostrar inventario, stock y kardex.", category=categories[cat].name,
            category_id=categories[cat].id, subcategory=sub, brand=brand, model=model_name,
            supplier_id=suppliers[supplier_key].id, barcode=f"DEMO-{key.upper()}-BARCODE",
            image_url="", location="Almacén demo · Pasillo A", active=True, unit=unit,
            quantity=Decimal(quantity), minimum_quantity=Decimal(minimum),
            restock_responsible_email="mario.guerrero@arcoenergy.mx", low_stock_alert_active=True,
            unit_cost=Decimal(cost), updated_at=now)

    # Opening stock plus purchase and consumption rows reconcile exactly to on-hand quantity.
    purchased_quantities = {"panel": 12, "rail": 20, "connector": 12, "cablepv": 100}
    consumed_quantities = {"panel": 8, "rail": 4, "clamp": 16}
    for item_key, item in items.items():
        opening_qty = Decimal(item.quantity)-Decimal(purchased_quantities.get(item_key, 0))+Decimal(consumed_quantities.get(item_key, 0))
        put(InventoryMovement, f"movement-opening-{item_key}", folio=f"DEMO-ENT-INI-{item_key.upper()}",
            source_key=f"demo-opening-stock-{item_key}", item_id=item.id, installation_id=None,
            project_id=None, quantity=opening_qty, movement_type="in", unit_cost=item.unit_cost,
            related_movement_id=None, supplier_id=None, invoice_reference="", purchase_line_id=None,
            work_order_material_id=None, source_type="manual", source_reference="DEMO-INVENTARIO-INICIAL",
            department="Almacén", reason="DEMO · Existencia inicial para conciliación de kardex.",
            created_by=DEMO_USER, created_at=now-timedelta(days=30))

    # Chart of accounts: separate DEMO branch to avoid overwriting company accounts.
    accounts = {}
    account_specs = [
        ("assets", "DM-1000", "DEMO · Activo", "asset", None, None, None, "operating", True),
        ("current", "DM-1100", "DEMO · Activo corriente", "asset", "assets", None, None, "operating", True),
        ("cash_group", "1110", "DEMO · Caja y bancos", "asset", "current", None, None, "operating", True),
        ("receivables", "DM-1120", "DEMO · Clientes por cobrar", "asset", "current", None, None, "operating", True),
        ("inventory_ledger", "DM-1130", "DEMO · Inventarios", "asset", "current", None, None, "operating", False),
        ("liabilities", "DM-2000", "DEMO · Pasivo", "liability", None, None, None, "operating", True),
        ("payables", "DM-2100", "DEMO · Proveedores", "liability", "liabilities", None, None, "operating", True),
        ("equity", "DM-3000", "DEMO · Patrimonio", "equity", None, None, None, "operating", True),
        ("capital", "DM-3100", "DEMO · Capital inicial", "equity", "equity", None, None, "operating", False),
        ("income", "DM-4000", "DEMO · Ingresos", "income", None, None, None, "operating", True),
        ("sales", "DM-4100", "DEMO · Venta de sistemas solares", "income", "income", None, None, "operating", False),
        ("cogs", "5000", "DEMO · Costo de venta", "expense", None, None, None, "operating", True),
        ("materials", "DM-5100", "DEMO · Materiales instalados", "expense", "cogs", None, None, "operating", False),
        ("opex", "DM-6000", "DEMO · Gastos de operación", "expense", None, None, None, "operating", True),
        ("travel", "DM-6100", "DEMO · Viáticos", "expense", "opex", None, None, "operating", False),
        ("financial_expense", "6100", "DEMO · Gastos financieros", "expense", None, None, None, "financing", False),
        ("personal", "6200", "DEMO · Gastos personales y otros", "expense", None, None, None, "operating", False),
    ]
    for key, code, name, typ, parent_key, customer_key, financial_key, flow, group in account_specs:
        existing_code = db.scalar(select(AccountingAccount).where(AccountingAccount.code == code))
        if existing_code is not None:
            # Reuse a standard chart code when the tenant already has it. Never rewrite
            # the customer's existing account metadata; demo postings remain tagged.
            accounts[key] = existing_code
            continue
        accounts[key] = put(AccountingAccount, f"account-{key}", code=code, name=name, account_type=typ,
            parent_id=accounts[parent_key].id if parent_key else None,
            linked_customer_id=customers[customer_key].id if customer_key else None,
            linked_financial_account_id=None, cash_flow_activity=flow, is_group=group,
            active=True, created_by=DEMO_USER, created_at=now-timedelta(days=40))

    fin_accounts = {}
    for key, name, typ, opening in [("cash", "DEMO · Caja chica", "cash", 12500),
                                   ("bank", "DEMO · Santander", "bank", 186000),
                                   ("bank2", "DEMO · Banco Azteca", "bank", 74000)]:
        fin_accounts[key] = put(FinancialAccount, f"financial-{key}", name=name, account_type=typ,
            opening_balance=Decimal(opening), opening_balance_date=today-timedelta(days=26), active=True,
            created_by=DEMO_USER, created_at=now-timedelta(days=40))
    for key, fin_key in [("cash_ledger", "cash"), ("santander_ledger", "bank"), ("azteca_ledger", "bank2")]:
        code = {"cash_ledger":"DM-1111", "santander_ledger":"DM-1112", "azteca_ledger":"DM-1113"}[key]
        name = {"cash_ledger":"DEMO · Caja chica", "santander_ledger":"DEMO · Santander", "azteca_ledger":"DEMO · Banco Azteca"}[key]
        accounts[key] = put(AccountingAccount, f"account-{key}", code=code, name=name, account_type="asset",
            parent_id=accounts["cash_group"].id, linked_customer_id=None,
            linked_financial_account_id=fin_accounts[fin_key].id, cash_flow_activity="operating",
            is_group=False, active=True, created_by=DEMO_USER, created_at=now-timedelta(days=40))
    for index, cust in enumerate(("mariana", "roberto", "fernando"), start=1):
        accounts[f"ar_{cust}"] = put(AccountingAccount, f"account-ar-{cust}", code=f"DM-112{index}",
            name=customers[cust].name, account_type="asset", parent_id=accounts["receivables"].id,
            linked_customer_id=customers[cust].id, linked_financial_account_id=None,
            cash_flow_activity="operating", is_group=False, active=True, created_by=DEMO_USER, created_at=now)
    for index, key in enumerate(("solar", "electrico"), start=1):
        accounts[f"ap_{key}"] = put(AccountingAccount, f"account-ap-{key}", code=f"DM-210{index}",
            name=suppliers[key].name, account_type="liability", parent_id=accounts["payables"].id,
            linked_customer_id=None, linked_financial_account_id=None, cash_flow_activity="operating",
            is_group=False, active=True, created_by=DEMO_USER, created_at=now)
    for key, fin_key in [("cash_ledger","cash"),("santander_ledger","bank"),("azteca_ledger","bank2")]:
        accounts[key].linked_financial_account_id = fin_accounts[fin_key].id

    # Quote-to-sale path and corresponding work order materials.
    sale_customers = ["mariana", "roberto", "fernando"]
    sales = {}
    for cust, qkey, sale_type in [("mariana", "quote-mariana", "cash"), ("roberto", "quote-roberto", "credit"), ("fernando", "quote-fernando", "credit")]:
        sale_id = _id(f"sale-{cust}")
        sales[cust] = put(Sale, f"sale-{cust}", folio=f"DEMO-VTA-{cust.upper()}-001",
            customer_id=customers[cust].id, quote_id=quotes[qkey].id, installation_id=installs[cust].id,
            sale_type=sale_type, total=quotes[qkey].total, created_by=DEMO_USER, created_at=now-timedelta(days=5))
    for cust in sale_customers:
        for item_key, requested, consumed in [("panel", 8 if cust=="mariana" else 12, 8 if cust=="mariana" else 0),
                                               ("rail", 8 if cust=="mariana" else 12, 4 if cust=="mariana" else 0),
                                               ("clamp", 32 if cust=="mariana" else 48, 16 if cust=="mariana" else 0)]:
            material = put(WorkOrderMaterial, f"work-material-{cust}-{item_key}", installation_id=installs[cust].id,
                item_id=items[item_key].id, requested_quantity=Decimal(requested),
                preissued_quantity=Decimal(consumed), consumed_quantity=Decimal(consumed),
                unit_cost=items[item_key].unit_cost, created_by=DEMO_USER, created_at=now-timedelta(days=4))
            if consumed:
                put(InventoryMovement, f"movement-consume-{cust}-{item_key}", folio=f"DEMO-CON-{cust.upper()}-{item_key.upper()}",
                    source_key=f"demo-consume-{cust}-{item_key}", item_id=items[item_key].id,
                    installation_id=installs[cust].id, project_id=projects[cust].id,
                    quantity=Decimal(consumed), movement_type="consumption", unit_cost=items[item_key].unit_cost,
                    related_movement_id=None, supplier_id=None, invoice_reference="", purchase_line_id=None,
                    work_order_material_id=material.id, source_type="work_order", source_reference=installs[cust].folio,
                    department="Instalación", reason="DEMO · Material utilizado en orden de trabajo.",
                    created_by=DEMO_USER, created_at=now-timedelta(days=3))

    # Purchases with a supplier credit balance and a partial supplier payment.
    purchase_specs = [("solar", "DEMO-COMP-001", "DEMO-FACT-001", "credit", 0.40),
                      ("electrico", "DEMO-COMP-002", "DEMO-FACT-002", "cash", 1.0)]
    purchases = {}
    purchase_line_for_item = {}
    for supplier_key, folio, invoice, terms, paid_ratio in purchase_specs:
        chosen = [("panel", 12), ("rail", 20)] if supplier_key=="solar" else [("connector", 12), ("cablepv", 100)]
        lines_total = sum(Decimal(qty)*items[item_key].unit_cost for item_key, qty in chosen)
        paid_amount = (lines_total*Decimal(str(paid_ratio))).quantize(Decimal("0.01"))
        purchases[supplier_key] = put(Purchase, f"purchase-{supplier_key}", folio=folio,
            supplier_id=suppliers[supplier_key].id, invoice_number=invoice, invoice_drive_file_id="",
            invoice_filename="", invoice_content_type="", invoice_updated_at=None,
            payment_terms=terms, purchase_date=today-timedelta(days=11),
            due_date=today+timedelta(days=19) if terms=="credit" else None,
            total=lines_total, paid_amount=paid_amount,
            status="partially_paid" if paid_amount < lines_total else "paid",
            created_by=DEMO_USER, created_at=now-timedelta(days=11))
        for idx, (item_key, qty) in enumerate(chosen, start=1):
            line = put(PurchaseLine, f"purchase-line-{supplier_key}-{item_key}", purchase_id=purchases[supplier_key].id,
                item_id=items[item_key].id, quantity=Decimal(qty), unit_cost=items[item_key].unit_cost,
                line_total=Decimal(qty)*items[item_key].unit_cost,
                previous_unit_cost=items[item_key].unit_cost-Decimal("5.00"))
            purchase_line_for_item[item_key] = line
            put(InventoryMovement, f"movement-purchase-{supplier_key}-{item_key}",
                folio=f"DEMO-ENT-{supplier_key.upper()}-{idx:02d}", source_key=f"demo-purchase-{supplier_key}-{item_key}",
                item_id=items[item_key].id, installation_id=None, project_id=projects["mariana"].id,
                quantity=Decimal(qty), movement_type="purchase", unit_cost=items[item_key].unit_cost,
                related_movement_id=None, supplier_id=suppliers[supplier_key].id,
                invoice_reference=invoice, purchase_line_id=line.id, work_order_material_id=None,
                source_type="purchase", source_reference=folio, department="Almacén",
                reason="DEMO · Compra recibida.", created_by=DEMO_USER, created_at=now-timedelta(days=11))

    # Customer credit schedule and payments reflected in bank/cash ledgers.
    receivables = {}
    for cust, amount, paid, due, inst_no in [
        ("roberto", Decimal("11300.00"), Decimal("2500.00"), -3, 1),
        ("roberto", Decimal("11300.00"), Decimal("0.00"), 8, 2),
        ("roberto", Decimal("11300.00"), Decimal("0.00"), 38, 3),
        ("roberto", Decimal("11300.00"), Decimal("0.00"), 68, 4),
        ("roberto", Decimal("11300.00"), Decimal("0.00"), 98, 5),
        ("roberto", Decimal("11300.00"), Decimal("0.00"), 128, 6),
        ("roberto", Decimal("11380.00"), Decimal("0.00"), 158, 7),
        ("fernando", Decimal("32000.00"), Decimal("1200.00"), 2, 1),
        ("fernando", Decimal("33000.00"), Decimal("0.00"), 32, 2),
        ("fernando", Decimal("33440.00"), Decimal("0.00"), 62, 3),
    ]:
        k = f"receivable-{cust}-{inst_no}"
        receivable = put(Receivable, k, customer_id=customers[cust].id,
            quote_id=quotes["quote-roberto" if cust=="roberto" else "quote-fernando"].id,
            installment_number=inst_no, due_date=today+timedelta(days=due), amount=amount,
            paid_amount=paid, status="paid" if paid>=amount else "overdue" if due<0 else "partial" if paid else "pending",
            payment_method="Transferencia", created_at=now-timedelta(days=20))
        receivables[k] = receivable

    # Opening accounts and posted journal rows are balanced and intentionally demo-labelled.
    def journal(key, folio, occurred, description, project, source_type, source_id, pairs):
        entry = put(AccountingEntry, f"entry-{key}", folio=folio, occurred_on=occurred,
            description=f"DEMO · {description}", reference=folio, project_id=project,
            source_type=source_type, source_id=source_id, status="posted", created_by=DEMO_USER,
            created_at=now)
        for idx, (account_key, customer_key, debit, credit, memo) in enumerate(pairs, start=1):
            put(AccountingLine, f"line-{key}-{idx}", entry_id=entry.id,
                account_id=accounts[account_key].id,
                customer_id=customers[customer_key].id if customer_key else None,
                memo=f"DEMO · {memo}", debit=Decimal(debit), credit=Decimal(credit))
        return entry

    # Opening balances: assets equal liabilities plus equity.
    opening_inventory_value = sum(
        (Decimal(item.quantity)-Decimal(purchased_quantities.get(key, 0))+Decimal(consumed_quantities.get(key, 0)))
        * Decimal(item.unit_cost) for key, item in items.items()
    )
    opening_assets = sum(Decimal(a.opening_balance) for a in fin_accounts.values()) + opening_inventory_value
    opening_liabilities = Decimal("0.00")
    opening_equity = opening_assets-opening_liabilities
    journal("opening", "DEMO-POL-OPEN-001", today-timedelta(days=26), "Saldos iniciales de ejemplo", None,
        "financial_account_opening", _id("entry-opening"), [
            ("santander_ledger", None, fin_accounts["bank"].opening_balance, 0, "Saldo inicial Santander"),
            ("azteca_ledger", None, fin_accounts["bank2"].opening_balance, 0, "Saldo inicial Banco Azteca"),
            ("cash_ledger", None, fin_accounts["cash"].opening_balance, 0, "Saldo inicial de caja"),
            ("inventory_ledger", None, opening_inventory_value, 0, "Valor inicial de inventario"),
            ("capital", None, 0, opening_equity, "Capital inicial"),
        ])

    demo_cash_movements = {}
    def cash(key, account_key, direction, amount, category, description, occurred, source_type, source_id):
        row = put(CashMovement, f"cash-{key}", account_id=fin_accounts[account_key].id,
            direction=direction, amount=Decimal(amount), category=category,
            description=f"DEMO · {description}", occurred_on=occurred, source_type=source_type,
            source_id=source_id, reversal_of_id=None, created_by=DEMO_USER, created_at=now)
        demo_cash_movements[key] = row
        return row

    for cust, account_key, amount in [("roberto", "bank", Decimal("2500.00")),
                                      ("fernando", "cash", Decimal("1200.00"))]:
        key = f"customer-payment-{cust}"
        cash(key, account_key, "in", amount, "Cobranza", f"Cobro demo a {customers[cust].name}", today-timedelta(days=2), "customer_payment", _id(key))
        rec_key = f"receivable-{cust}-1"
        put(CustomerPayment, key, receivable_id=receivables[rec_key].id,
            account_id=fin_accounts[account_key].id, cash_movement_id=demo_cash_movements[key].id,
            amount=Decimal(amount), paid_on=today-timedelta(days=2), reference=f"DEMO-COB-{cust.upper()}",
            reversal_of_id=None, created_by=DEMO_USER, created_at=now)
        cust_key = "ar_roberto" if cust=="roberto" else "ar_fernando"
        journal(key, f"DEMO-POL-COB-{cust.upper()}", today-timedelta(days=2), "Cobro de cuota", projects[cust].id,
            "demo_customer_payment", _id(key), [("santander_ledger" if account_key=="bank" else "cash_ledger", None, amount, 0, "Entrada de dinero"),
            (cust_key, cust, 0, amount, "Abono a cuenta del cliente")])

    for cust, qkey, account_key in [("mariana", "quote-mariana", "bank"), ("roberto", "quote-roberto", "bank"), ("fernando", "quote-fernando", "bank")]:
        amount = Decimal(quotes[qkey].total)
        if cust=="mariana":
            cash(f"sale-{cust}", account_key, "in", amount, "Venta", "Liquidación de sistema solar", today-timedelta(days=5), "sale", sales[cust].id)
            journal(f"sale-{cust}", f"DEMO-POL-VTA-{cust.upper()}", today-timedelta(days=5), "Venta de sistema solar", projects[cust].id,
                "demo_sale", sales[cust].id, [("santander_ledger", None, amount, 0, "Cobro de contado"),
                ("sales", None, 0, amount, "Ingreso por venta")])
        else:
            receivable_account = "ar_roberto" if cust=="roberto" else "ar_fernando"
            journal(f"sale-{cust}", f"DEMO-POL-VTA-{cust.upper()}", today-timedelta(days=5), "Venta financiada de sistema solar", projects[cust].id,
                "demo_sale", sales[cust].id, [(receivable_account, cust, amount, 0, "Cuenta por cobrar"),
                ("sales", None, 0, amount, "Ingreso por venta")])

    for supplier_key, account_key in [("solar", "bank"), ("electrico", "cash")]:
        p = purchases[supplier_key]
        payable = Decimal(p.total)-Decimal(p.paid_amount)
        supplier_account = "ap_solar" if supplier_key=="solar" else "ap_electrico"
        journal(f"purchase-{supplier_key}", f"DEMO-POL-COMP-{supplier_key.upper()}", p.purchase_date,
            "Compra de materiales para almacén", projects["mariana"].id, "demo_purchase", p.id,
            [("inventory_ledger", None, p.total, 0, "Entrada al inventario"),
             (supplier_account, None, 0, payable, "Saldo con proveedor"),
             ("santander_ledger" if account_key=="bank" else "cash_ledger", None, 0, p.paid_amount, "Pago parcial de compra")])
        if p.paid_amount:
            movement = cash(f"supplier-payment-{supplier_key}", account_key, "out", p.paid_amount,
                "Pago a proveedor", f"Pago de compra a {suppliers[supplier_key].name}", today-timedelta(days=10),
                "supplier_payment", _id(f"supplier-payment-{supplier_key}"))
            put(SupplierPayment, f"supplier-payment-{supplier_key}", purchase_id=p.id,
                account_id=fin_accounts[account_key].id, cash_movement_id=movement.id,
                amount=p.paid_amount, paid_on=today-timedelta(days=10), reference=f"DEMO-TR-{supplier_key.upper()}",
                reversal_of_id=None, created_by=DEMO_USER, created_at=now)

    expense_specs = [
        ("fuel", "mariana", "Viáticos", "variable", "Combustible de traslado a instalación", 1450, "cash", "travel"),
        ("commission", "roberto", "Comisiones bancarias", "variable", "Comisión de apertura del financiamiento", 890, "bank", "financial_expense"),
        ("owner_draw", None, "Otro", "unclassified", "Retiro personal de socio, no operativo", 9800, "bank", "personal"),
    ]
    for key, project_key, category, etype, description, amount, account_key, ledger_key in expense_specs:
        expense = put(ProjectExpense, f"expense-{key}", installation_id=installs[project_key].id if project_key else None,
            project_id=projects[project_key].id if project_key else None, category=category,
            expense_type=etype, description=f"DEMO · {description}", amount=Decimal(amount),
            occurred_on=today-timedelta(days=1 if key!="rent" else 7), receipt_url="",
            receipt_drive_file_id="", receipt_filename="", receipt_content_type="", receipt_updated_at=None,
            account_id=fin_accounts[account_key].id, reversal_of_id=None, created_by=DEMO_USER, created_at=now)
        cash(f"expense-{key}", account_key, "out", amount, category, description,
             today-timedelta(days=1 if key!="rent" else 7), "expense", expense.id)
        journal(f"expense-{key}", f"DEMO-POL-GASTO-{key.upper()}", expense.occurred_on,
            description, projects[project_key].id if project_key else None,
            "demo_expense", expense.id, [(ledger_key, None, amount, 0, category),
            ("cash_ledger" if account_key=="cash" else "santander_ledger", None, 0, amount, "Salida de dinero")])

    # Material cost recognized for completed work; a separate accounting impact.
    consumed_cost = sum(Decimal(items[k].unit_cost)*Decimal(q) for k, q in [("panel",8),("rail",4),("clamp",16)])
    journal("material-cost", "DEMO-POL-COSTO-001", today-timedelta(days=3), "Costo de materiales consumidos en instalación",
        projects["mariana"].id, "demo_material_cost", _id("material-cost"),
        [("materials", None, consumed_cost, 0, "Costo directo de instalación"),
         ("inventory_ledger", None, 0, consumed_cost, "Salida valorizada del almacén")])

    # Append-only profitability adjustments for a return and a customer bonification example.
    put(ProfitabilityAdjustment, "adjustment-return", installation_id=installs["mariana"].id,
        adjustment_type="return", description="DEMO · Bonificación por ajuste menor de instalación",
        amount=Decimal("850.00"), occurred_on=today-timedelta(days=1), reversal_of_id=None,
        created_by=DEMO_USER, created_at=now)
    put(ProfitabilityAdjustment, "adjustment-bonus", installation_id=installs["fernando"].id,
        adjustment_type="bonification", description="DEMO · Devolución aplicada a proyecto terminado",
        amount=Decimal("450.00"), occurred_on=today-timedelta(days=6), reversal_of_id=None,
        created_by=DEMO_USER, created_at=now)

    # A clearly synthetic batch record is useful in the inventory-import view.
    import_key = "inventory-import-batch"
    import_row = db.get(InventoryImportBatch, _id(import_key))
    if import_row is None:
        put(InventoryImportBatch, import_key, source_sha256="a"*64,
            source_filename="DEMO-inventario-de-muestra.csv",
            summary={"demo": True, "items": len(items), "message": "Datos ficticios de demostración"},
            imported_by=DEMO_USER, imported_at=now-timedelta(days=9))

    db.flush()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed repeatable DEV-only ArcoEnergy mock data")
    parser.add_argument("--apply", action="store_true", help="write/update the DEMO rows")
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env.casefold() not in {"dev", "development"}:
        raise SystemExit("Refusing to seed: APP_ENV must be dev or development.")
    if not args.apply:
        raise SystemExit("No writes made. Re-run with --apply to seed DEV mock data.")
    engine = create_database_engine()
    with Session(engine) as db, db.begin():
        counts = seed(db)
    print("DEV mock data seeded successfully (idempotent; no real rows deleted).")
    for model, count in sorted(counts.items()):
        print(f"{model}: {count}")


if __name__ == "__main__":
    main()
