"""Financial-only chart of accounts and balanced journals.

Revision ID: 202611240162
Revises: 202611240161
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611240162"
down_revision = "202611240161"
branch_labels = None
depends_on = None


def _record_cards(bind):
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    cards = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    existing = {row[0] for row in bind.execute(sa.select(cards.c.story_id)).all()}
    if not sa.inspect(bind).has_table("ae_history_card_reviews"):
        return
    reviews = sa.Table("ae_history_card_reviews", sa.MetaData(), autoload_with=bind)
    now = datetime.now(timezone.utc)
    rows = [
        {
            "story_id": "US-47", "iteration": "Contabilidad · balance y cobranza",
            "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar",
            "requested_by": "Stakeholder Arco Energy · solicitante por confirmar",
            "source_literal": "el segundo goal es que necesito que agregues para el modulo de contabilidad una hoja con forma de balance general; este balance general va a poder agregar secciones; cuentas; y subcuentas. en donde vamos a ser capaces de agregar la cuenta de cuentas por cobrar y subcuentas que serian los nombres de los clientes. despues cuando damos click a las subcuentas se abre los modals con el reporte de movimientos de ese cliente. /goal [Image #1] ademas de agregar un calendario al modulo de cobranza donde vemos los clientes y vemos cuando es el siguiente pago, su saldo actual, su reporte de movimientos. eso seria en el modulo de cobranza y el de estados de resultados seria en el modulo de contabilidad. tomalo como /goal",
            "source_reference": "Conversación Arco Energy · segundo goal contable · 24/11/2026",
            "normalized_story": "Como contador, quiero consultar y administrar un balance general jerárquico con secciones, cuentas y subcuentas por cliente, ver los movimientos de cada cliente, y consultar la cartera en un calendario para dar seguimiento a próximos pagos y saldos.",
            "acceptance_criteria": ["Balance al corte con secciones, cuentas y subcuentas.", "Se pueden crear cuentas y subcuentas desde Contabilidad.", "Cuentas por cobrar puede desglosarse por cliente.", "Al abrir una subcuenta de cliente se muestra su reporte de movimientos.", "Cobranza ofrece calendario con próximo pago, saldo y movimientos del cliente.", "Estado de resultados está en Contabilidad."],
        },
        {
            "story_id": "US-48", "iteration": "Contabilidad · cargos, abonos y bancos",
            "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar",
            "requested_by": "Stakeholder Arco Energy · solicitante por confirmar",
            "source_literal": "como tercer goal tambien vamos a tener las subcuentas de tarjetas que seria santander, banco azteca, etc. esa iria en la cuenta bancos y tambien ya deberia estar en el balance general; las cuentas y subcuentas se agregan directamente desde el balance general en el modulo contabilidad. y como un sistema contable tienen que tener igualmente cargos y abonos. tomalo como /goal",
            "source_reference": "Conversación Arco Energy · tercer goal contable · 24/11/2026",
            "normalized_story": "Como contador, quiero organizar caja y bancos por subcuentas de banco o tarjeta y registrar cada movimiento mediante cargos y abonos balanceados para que los estados financieros reflejen la contabilidad capturada.",
            "acceptance_criteria": ["Bancos contiene subcuentas independientes por institución o tarjeta.", "Las cuentas y subcuentas se crean desde el balance general.", "Cada movimiento conserva fecha, folio, descripción, referencia y proyecto opcional.", "Cada asiento exige al menos dos renglones y cargos iguales a abonos.", "Un asiento publicado no cambia inventario, ventas ni operaciones; modifica únicamente el mayor financiero.", "Balance, resultados y flujo se derivan del mismo mayor."],
        },
        {
            "story_id": "US-49", "iteration": "Contabilidad · proyectos y estado de resultados",
            "stakeholder": "Mario Groso · contador",
            "requested_by": "Mario Groso",
            "source_literal": "a su vamos a necesitar el modulod de proyectos, donde cada proyecto tiene relacionado pues su factura; sus ventas; sus gastos que es lo mas importante >GASTOS FINANCIEROS: Intereses y comisiones bancarias >GASTO PERSONALE Y OTROS: Son aquellos que no tienen nada que ver con la operación, estos no entran en los estados financieros si no hasta el final, como quien dice se restan ya despues del resultado Ok esa ya fue la separación de ingresos y egresos como puedes ver todo nace de los estados de cuenta de lo que nos va apareciendo entonces por así decirlo luego luego empezando quiero mi botonsote de \"REGISTRAR MOVIMIENTO y asi vamos a poder tener el segundo estado financiero que seria el estado de resultados en forma de reporte tambien",
            "source_reference": "WhatsApp Mario Groso · 5/11/2026 · 1:16 p.m. y mensaje posterior",
            "normalized_story": "Como contador, quiero registrar movimientos financieros vinculables a proyectos y emitir un estado de resultados por periodo o proyecto que separe ingresos, costo de venta, gastos operativos, financieros y personales/otros, para revisar el resultado con el criterio acordado.",
            "acceptance_criteria": ["Existe una acción visible REGISTRAR MOVIMIENTO.", "Los asientos pueden relacionarse con proyectos.", "El estado de resultados separa ingresos, costo de venta y gastos de operación.", "Los gastos financieros se muestran en su renglón separado.", "Gastos personales y otros se muestran después del resultado operativo.", "El filtro acepta periodo y proyecto.", "El reporte solo incorpora movimientos contables publicados."],
        },
    ]
    for row in rows:
        card = bind.execute(sa.select(cards).where(cards.c.story_id == row["story_id"]).order_by(cards.c.version.desc()).limit(1)).mappings().first() if row["story_id"] in existing else None
        if card is None:
            card_id = str(uuid4())
            bind.execute(cards.insert().values(
                id=card_id, version=1, source_type="conversation", source_language="es",
                source_artifact={"type": "conversation", "captured_as": "literal"},
                source_attribution=row["stakeholder"], source_confidence="direct_quote",
                source_links=[], unresolved_questions=[], linked_cards=[], recorded_by="Codex · implementación",
                created_at=now, **row,
            ))
            version = 1
        else:
            card_id, version = card["id"], card["version"]
        if bind.execute(sa.select(reviews.c.id).where(reviews.c.story_id == row["story_id"], reviews.c.story_version == version).limit(1)).first():
            continue
        review_version = (bind.execute(sa.select(sa.func.max(reviews.c.review_version)).where(reviews.c.story_id == row["story_id"])).scalar_one_or_none() or 0) + 1
        bind.execute(reviews.insert().values(
            id=str(uuid4()), story_id=row["story_id"], history_card_id=card_id, story_version=version,
            review_version=review_version,
            checklist=[{"criterion": criterion, "checked": False} for criterion in row["acceptance_criteria"]],
            observations="Pendiente de revisión funcional con el stakeholder.", finished=False,
            solution_proposed={
                "US-47": "Se agregó Balance general dentro de Contabilidad, árbol de cuentas y subcuentas por cliente, mayor por subcuenta y calendario mensual de cobranza con saldos y pagos.",
                "US-48": "Se agregó un mayor financiero de pólizas balanceadas, vinculación de caja/bancos, subcuentas y estados derivados del mismo conjunto de cargos y abonos. Las pólizas afectan solo el libro financiero.",
                "US-49": "Se agregó Registrar movimiento, vínculo opcional a proyecto, estado de resultados por periodo/proyecto y flujo clasificado. Ventas nuevas, cobranza y saldos de apertura generan pólizas. La automatización de consumos, compras y gastos queda pendiente de la clasificación confirmada por el contador.",
            }[row["story_id"]],
            reviewed_by="Codex · implementación", created_at=now,
        ))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    # The initial domain revision uses Base.metadata.create_all(), so clean
    # installs may already have these latest model tables before reaching 162.
    if not inspector.has_table("ae_accounting_accounts"):
        op.create_table(
        "ae_accounting_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("account_type", sa.String(20), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("ae_accounting_accounts.id"), nullable=True),
        sa.Column("linked_customer_id", sa.String(36), sa.ForeignKey("ae_customers.id"), nullable=True),
        sa.Column("linked_financial_account_id", sa.String(36), sa.ForeignKey("ae_financial_accounts.id"), nullable=True),
        sa.Column("cash_flow_activity", sa.String(20), nullable=False, server_default="operating"),
        sa.Column("is_group", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.String(180), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_ae_accounting_account_code"),
        )
    existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("ae_accounting_accounts")}
    for name, columns in (
        ("ix_ae_accounting_accounts_parent", ["parent_id"]),
        ("ix_ae_accounting_accounts_linked_customer_id", ["linked_customer_id"]),
        ("ix_ae_accounting_accounts_linked_financial_account_id", ["linked_financial_account_id"]),
    ):
        if name not in existing_indexes:
            op.create_index(name, "ae_accounting_accounts", columns)
    if not sa.inspect(bind).has_table("ae_accounting_entries"):
        op.create_table(
        "ae_accounting_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("folio", sa.String(40), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("reference", sa.String(180), nullable=False, server_default=""),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("ae_projects.id"), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=False, server_default="manual"),
        sa.Column("source_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="posted"),
        sa.Column("created_by", sa.String(180), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("folio", name="uq_ae_accounting_entry_folio"),
        sa.UniqueConstraint("source_type", "source_id", name="uq_ae_accounting_entry_source"),
        )
    existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("ae_accounting_entries")}
    for name, columns in (
        ("ix_ae_accounting_entries_occurred_on", ["occurred_on"]),
        ("ix_ae_accounting_entries_project_id", ["project_id"]),
    ):
        if name not in existing_indexes:
            op.create_index(name, "ae_accounting_entries", columns)
    if not sa.inspect(bind).has_table("ae_accounting_lines"):
        op.create_table(
        "ae_accounting_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("ae_accounting_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("ae_accounting_accounts.id"), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("ae_customers.id"), nullable=True),
        sa.Column("memo", sa.String(240), nullable=False, server_default=""),
        sa.Column("debit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        )
    existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("ae_accounting_lines")}
    for name, columns in (
        ("ix_ae_accounting_lines_entry_id", ["entry_id"]),
        ("ix_ae_accounting_lines_account", ["account_id"]),
        ("ix_ae_accounting_lines_customer", ["customer_id"]),
    ):
        if name not in existing_indexes:
            op.create_index(name, "ae_accounting_lines", columns)
    accounts = sa.Table("ae_accounting_accounts", sa.MetaData(), autoload_with=bind)
    seed = [
        ("1000", "Activo", "asset", None, True),
        ("1100", "Activo corriente", "asset", "1000", True),
        ("1110", "Caja y bancos", "asset", "1100", True),
        ("1120", "Cuentas por cobrar", "asset", "1100", True),
        ("1130", "Inventarios", "asset", "1100", False),
        ("1200", "Activo no corriente", "asset", "1000", True),
        ("2000", "Pasivo", "liability", None, True),
        ("2100", "Pasivo corriente", "liability", "2000", True),
        ("2200", "Pasivo no corriente", "liability", "2000", True),
        ("3000", "Patrimonio", "equity", None, True),
        ("3001", "Saldos iniciales y aportaciones", "equity", "3000", False),
        ("4000", "Ingresos", "income", None, True),
        ("4100", "Ventas de sistemas solares", "income", "4000", False),
        ("5000", "Costo de venta", "expense", None, True),
        ("6000", "Gastos de operación", "expense", None, True),
        ("6100", "Gastos financieros", "expense", None, True),
        ("6200", "Gastos personales y otros", "expense", None, True),
    ]
    ids = {code: str(uuid4()) for code, *_ in seed}
    for code, name, account_type, parent_code, is_group in seed:
        bind.execute(accounts.insert().values(
            id=ids[code], code=code, name=name, account_type=account_type,
            parent_id=ids.get(parent_code) if parent_code else None,
            cash_flow_activity="exclude" if account_type in ("asset", "equity") else "operating",
            is_group=is_group, active=True, created_by="system",
            created_at=datetime.now(timezone.utc),
        ))
    financial_accounts = sa.Table("ae_financial_accounts", sa.MetaData(), autoload_with=bind)
    accounting_entries = sa.Table("ae_accounting_entries", sa.MetaData(), autoload_with=bind)
    accounting_lines = sa.Table("ae_accounting_lines", sa.MetaData(), autoload_with=bind)
    cash_movements = sa.Table("ae_cash_movements", sa.MetaData(), autoload_with=bind) if sa.inspect(bind).has_table("ae_cash_movements") else None
    for account in bind.execute(sa.select(financial_accounts)).mappings():
        bank_leaf_id = str(uuid4())
        bind.execute(accounts.insert().values(
            id=bank_leaf_id, code=f"1110-{account['id'][:12]}", name=account["name"],
            account_type="asset", parent_id=ids["1110"], linked_financial_account_id=account["id"],
            cash_flow_activity="exclude", is_group=False, active=bool(account.get("active", True)),
            created_by="system", created_at=datetime.now(timezone.utc),
        ))
        amount = account.get("opening_balance") or 0
        if cash_movements is not None:
            for movement in bind.execute(sa.select(cash_movements).where(cash_movements.c.account_id == account["id"])).mappings():
                amount += movement["amount"] if movement["direction"] == "in" else -movement["amount"]
        if amount != 0:
            occurred_on = datetime.now(timezone.utc).date()
            entry_id = str(uuid4())
            bind.execute(accounting_entries.insert().values(
                id=entry_id, folio=f"ASI-{occurred_on:%y%m%d}-{uuid4().hex[:6].upper()}",
                occurred_on=occurred_on, description=f"Saldo inicial de {account['name']}",
                reference="Apertura de cuenta financiera", source_type="financial_account_opening",
                source_id=account["id"], status="posted", created_by="system", created_at=datetime.now(timezone.utc),
            ))
            bind.execute(accounting_lines.insert(), [
                {"id": str(uuid4()), "entry_id": entry_id, "account_id": bank_leaf_id, "customer_id": None, "memo": "Saldo al abrir el mayor", "debit": amount if amount > 0 else 0, "credit": -amount if amount < 0 else 0},
                {"id": str(uuid4()), "entry_id": entry_id, "account_id": ids["3001"], "customer_id": None, "memo": "Contrapartida de apertura", "debit": -amount if amount < 0 else 0, "credit": amount if amount > 0 else 0},
            ])
    customers = sa.Table("ae_customers", sa.MetaData(), autoload_with=bind)
    customer_account_ids = {}
    for customer in bind.execute(sa.select(customers)).mappings():
        customer_leaf_id = str(uuid4())
        customer_account_ids[customer["id"]] = customer_leaf_id
        bind.execute(accounts.insert().values(
            id=customer_leaf_id, code=f"1120-{customer['id'][:12]}", name=customer["name"],
            account_type="asset", parent_id=ids["1120"], linked_customer_id=customer["id"],
            cash_flow_activity="operating", is_group=False, active=True,
            created_by="system", created_at=datetime.now(timezone.utc),
        ))
    if sa.inspect(bind).has_table("ae_receivables"):
        receivables = sa.Table("ae_receivables", sa.MetaData(), autoload_with=bind)
        open_by_customer = {}
        for receivable in bind.execute(sa.select(receivables)).mappings():
            balance = (receivable["amount"] or 0) - (receivable["paid_amount"] or 0)
            if balance > 0 and receivable["status"] not in ("paid", "cancelled"):
                customer_id = receivable["customer_id"]
                open_by_customer[customer_id] = open_by_customer.get(customer_id, 0) + balance
        for customer_id, amount in open_by_customer.items():
            if amount <= 0 or customer_id not in customer_account_ids:
                continue
            occurred_on = datetime.now(timezone.utc).date()
            entry_id = str(uuid4())
            bind.execute(accounting_entries.insert().values(
                id=entry_id, folio=f"ASI-{occurred_on:%y%m%d}-{uuid4().hex[:6].upper()}",
                occurred_on=occurred_on, description="Saldo de cartera al abrir el mayor",
                reference=f"Cuenta por cobrar · {customer_id}", source_type="receivable_opening",
                source_id=customer_id, status="posted", created_by="system", created_at=datetime.now(timezone.utc),
            ))
            bind.execute(accounting_lines.insert(), [
                {"id": str(uuid4()), "entry_id": entry_id, "account_id": customer_account_ids[customer_id], "customer_id": customer_id, "memo": "Saldo inicial de cartera", "debit": amount, "credit": 0},
                {"id": str(uuid4()), "entry_id": entry_id, "account_id": ids["3001"], "customer_id": None, "memo": "Contrapartida de apertura de cartera", "debit": 0, "credit": amount},
            ])
    if sa.inspect(bind).has_table("ae_inventory"):
        inventory = sa.Table("ae_inventory", sa.MetaData(), autoload_with=bind)
        inventory_value = bind.execute(sa.select(sa.func.coalesce(sa.func.sum(inventory.c.quantity * inventory.c.unit_cost), 0))).scalar_one()
        if inventory_value > 0:
            inventory_account_id = str(uuid4())
            bind.execute(accounts.insert().values(
                id=inventory_account_id, code="1130-OPEN", name="Inventario al iniciar el mayor",
                account_type="asset", parent_id=ids["1130"], cash_flow_activity="exclude", is_group=False,
                active=True, created_by="system", created_at=datetime.now(timezone.utc),
            ))
            occurred_on = datetime.now(timezone.utc).date()
            entry_id = str(uuid4())
            bind.execute(accounting_entries.insert().values(
                id=entry_id, folio=f"ASI-{occurred_on:%y%m%d}-{uuid4().hex[:6].upper()}",
                occurred_on=occurred_on, description="Valuación de inventario al abrir el mayor",
                reference="Existencias del almacén", source_type="inventory_opening", source_id="catalog-snapshot",
                status="posted", created_by="system", created_at=datetime.now(timezone.utc),
            ))
            bind.execute(accounting_lines.insert(), [
                {"id": str(uuid4()), "entry_id": entry_id, "account_id": inventory_account_id, "customer_id": None, "memo": "Existencia valorizada", "debit": inventory_value, "credit": 0},
                {"id": str(uuid4()), "entry_id": entry_id, "account_id": ids["3001"], "customer_id": None, "memo": "Contrapartida de apertura de inventario", "debit": 0, "credit": inventory_value},
            ])
    _record_cards(bind)


def downgrade():
    # Entries are financial records; retain tables on downgrade to avoid deleting them.
    pass
