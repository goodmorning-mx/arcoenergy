"""Register the requested Arco Energy module views and financial transaction flow.

Revision ID: 202611270163
Revises: 202611240162
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611270163"
down_revision = "202611240162"
branch_labels = None
depends_on = None

CARDS = [
    {
        "story_id": "US-50", "iteration": "CRM · cobranza por calendario y cliente",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "primero quita estos 2 recuadros de cobranza. hasta arriba debe ir el calendario hasta arriba; despues debajo debe ir las tarjetas de los clientes a cobrar proximamente con su deuda pendiente, en forma de cards cada uno.",
        "normalized_story": "Como persona de cobranza, quiero ver primero el calendario mensual y debajo tarjetas agrupadas por cliente con deuda pendiente, próximo vencimiento, movimientos, pago y recordatorio.",
        "acceptance_criteria": ["El calendario es el primer contenido del módulo y no aparecen el formulario anterior ni la tabla de agenda.", "Los clientes con saldo se muestran en tarjetas agrupadas por persona.", "Cada tarjeta muestra saldo abierto y próximo vencimiento.", "Desde la tarjeta se puede consultar movimientos, detalle de cuota, registrar pago y abrir WhatsApp cuando hay teléfono.", "Seleccionar una fecha del calendario filtra las tarjetas a los vencimientos del día y permite volver a todos."],
        "solution": "Se retiraron los dos paneles previos. Cobranza abre directamente el calendario y presenta debajo cartera agrupada en cards con saldo, fecha, detalle, registro de pagos, movimientos y recordatorio WhatsApp.",
    },
    {
        "story_id": "US-51", "iteration": "CRM · bitácora de gastos y póliza automática",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "en el modulo de gastos lo vamos a hacer en forma de tabla; con un bonito UI utiliza alguna tabla de material UI [Image #1] /goal. los gastos tambien deben reflejar la contabilidad entonces igual manera se pregunta la categoria, el proyecto, y el metodo de gasto de que cuenta sale, ese modal de cuentas nos va a servir porque es reutilizable, el chiste es que reflejen las operaciones financieras, e impacten los estados financieros para que puedan ser proyectados al dia.",
        "normalized_story": "Como contador y administrador, quiero registrar y revisar gastos en una tabla filtrable, seleccionar categoría, proyecto y cuenta pagadora, y reflejar la operación con doble partida en los estados financieros.",
        "acceptance_criteria": ["El módulo de gastos presenta una tabla con búsqueda y filtros de categoría y tipo.", "El alta se realiza en un modal e incluye fecha, categoría, tipo, descripción, importe, proyecto/orden, cuenta y comprobante.", "La cuenta pagadora es obligatoria y puede ser caja/efectivo o banco.", "El gasto registra caja/banco y una póliza balanceada enlazada al proyecto.", "La categoría deriva al grupo de costo de venta, gasto operativo, financiero o personal/otro.", "La corrección conserva el original y crea movimientos compensatorios tanto en caja como en el mayor."],
        "solution": "Se convirtió Gastos en una tabla con filtros y alta en modal; cada gasto exige cuenta pagadora y crea una póliza débito a gasto / crédito a caja-banco. La corrección agrega reversas append-only de caja y contabilidad.",
    },
    {
        "story_id": "US-52", "iteration": "CRM · directorio de clientes en tarjetas",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "en el modulo de clientes pues deben ir los clientes tambien en formas de tarjetas cuadradas como material UI [Image #1]",
        "normalized_story": "Como usuario del CRM, quiero consultar clientes en tarjetas cuadradas de lectura rápida y abrir desde cada tarjeta su ficha completa.",
        "acceptance_criteria": ["Cada cliente se presenta en una tarjeta dentro de una cuadrícula responsiva.", "La tarjeta muestra nombre, estado, ciudad, teléfono, correo y origen.", "La búsqueda filtra las tarjetas.", "Al seleccionar una tarjeta se abre la ficha de cliente existente."],
        "solution": "El directorio se presenta como una cuadrícula responsiva de tarjetas con datos de contacto y estado; la selección reutiliza el drawer de ficha existente.",
    },
    {
        "story_id": "US-53", "iteration": "CRM · ventas en tarjetas y gráfica por periodo",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "las ventas de igual manera deben ir en forma de tarjeta, ademas agrega hasta arriba un grafico de barras por semana por mes y por anio [Image #1] /goal",
        "normalized_story": "Como administrador, quiero visualizar ventas como tarjetas y comparar montos en una gráfica de barras semanal, mensual o anual.",
        "acceptance_criteria": ["La gráfica aparece antes de las ventas y permite cambiar Semana, Mes y Año.", "Los importes de cada periodo se calculan desde ventas registradas y excluyen las ventas corregidas.", "Cada venta aparece en tarjeta con folio, cliente, orden, método/tipo, materiales, fecha y total.", "Se conserva la acción autorizada de corregir venta."],
        "solution": "Se agregó una gráfica de barras responsiva con selección semanal, mensual y anual; las ventas se muestran en tarjetas con su orden, cliente, forma de cobro, materiales y acción de corrección.",
    },
    {
        "story_id": "US-54", "iteration": "CRM · proyectos en tarjetas",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "los proyectos es nuestra parte mas importante tambien necesito que le des formato de tarjeta [Image #1] /goal",
        "normalized_story": "Como coordinador, quiero revisar los proyectos como tarjetas y localizar su folio, cliente, estado y órdenes vinculadas.",
        "acceptance_criteria": ["Los proyectos se presentan como cards adaptables con código/folio, nombre, cliente y ciudad.", "Cada tarjeta presenta estado, órdenes asociadas, fecha e instrucciones/notas.", "Hay búsqueda por folio, proyecto, cliente o ciudad.", "Crear proyecto queda disponible desde un modal."],
        "solution": "El listado tabular se sustituyó por cards de proyecto con folio, cliente, ubicación, estado y órdenes; el alta queda en modal y se agregó búsqueda.",
    },
    {
        "story_id": "US-55", "iteration": "CRM · tablero de instalaciones",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "las instalaciones las vamos a poner como columnas horizontales donde simplemente tenemos 3 que serian pendientes; en progreso, y terminadas. [Image #1]/goal",
        "normalized_story": "Como coordinador de campo, quiero ver las órdenes en un tablero horizontal de pendientes, en progreso y terminadas para ubicar rápidamente la carga de trabajo.",
        "acceptance_criteria": ["El tablero muestra tres columnas horizontales: Pendientes, En progreso y Terminadas.", "Cada tarjeta presenta cliente, folio/proyecto, contacto, fecha, cuadrilla y disponibilidad/consumo de material.", "La etapa se deriva del estado de la orden, checklist operativo y consumo registrado.", "La asignación de una orden está disponible desde un modal y conserva su vínculo con PWA/instaladores."],
        "solution": "Instalaciones se reorganizó como Kanban horizontal de tres columnas. Las tarjetas conservan datos de contacto, cuadrilla, agenda y materiales; la asignación se realiza desde modal.",
    },
    {
        "story_id": "US-56", "iteration": "CRM · venta guiada y selección contable",
        "stakeholder": "Stakeholder Arco Energy · solicitante por confirmar", "requested_by": "Usuario Arco Energy · solicitante por confirmar",
        "source_literal": "ahora, segun el modulo de contabilidad; todas las operaciones representan su igual en la contabilidad; entonces necesitaos que por ejemplo al agregar una venta forzosamente se pregunte el metodo de pago, no quiero un modal, sino slides en el modal donde primero registras al cliente, despues el monto, y despues con iconos vas a registrar en que cuenta se van a reflejar de la contabilidad si bancos, efectivo, clientes. [Image #1]",
        "normalized_story": "Como vendedor, quiero registrar la venta mediante pasos sucesivos y elegir de forma obligatoria si el ingreso corresponde a efectivo, banco o cuenta por cobrar para que la operación afecte el libro financiero correcto.",
        "acceptance_criteria": ["El modal avanza por cliente/propuesta, monto, método/cuenta y orden.", "No se puede avanzar sin cotización aprobada ni sin método de pago.", "Efectivo y bancos listan únicamente cuentas del tipo elegido y exigen una cuenta específica.", "Clientes por cobrar solicita fecha y condiciones de cuotas.", "La venta registra caja/receivable e iguala el cargo con el abono de ingreso en una póliza vinculada al proyecto.", "El usuario ve el impacto antes de confirmar."],
        "solution": "El alta de venta usa un wizard en cuatro pasos: cliente/cotización, monto aprobado, selección visual de efectivo/bancos/cuentas por cobrar y datos de orden; las opciones de cuenta se filtran por tipo y se informa el impacto contable.",
    },
]


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ae_history_cards") or not inspector.has_table("ae_history_card_reviews"):
        return
    cards = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    reviews = sa.Table("ae_history_card_reviews", sa.MetaData(), autoload_with=bind)
    now = datetime.now(timezone.utc)
    for row in CARDS:
        existing = bind.execute(sa.select(cards).where(cards.c.story_id == row["story_id"]).order_by(cards.c.version.desc()).limit(1)).mappings().first()
        if existing:
            card_id, version = existing["id"], existing["version"]
        else:
            card_id, version = str(uuid4()), 1
            bind.execute(cards.insert().values(
                id=card_id, version=version, source_type="conversation", source_language="es",
                source_artifact={"type":"conversation","captured_as":"literal","reference":"Conversación Arco Energy · Iteración de módulos CRM · 27/11/2026"},
                source_attribution=row["stakeholder"], source_confidence="direct_quote", source_links=[],
                unresolved_questions=[], linked_cards=[], recorded_by="Codex · implementación", created_at=now,
                source_reference="Conversación Arco Energy · Iteración de módulos CRM · 27/11/2026",
                acceptance_criteria=row["acceptance_criteria"], **{k:v for k,v in row.items() if k!="acceptance_criteria" and k!="solution"},
            ))
        reviewed = bind.execute(sa.select(reviews.c.id).where(reviews.c.story_id == row["story_id"], reviews.c.story_version == version).limit(1)).first()
        if reviewed:
            continue
        review_version=(bind.execute(sa.select(sa.func.max(reviews.c.review_version)).where(reviews.c.story_id==row["story_id"])).scalar_one_or_none() or 0)+1
        bind.execute(reviews.insert().values(
            id=str(uuid4()),story_id=row["story_id"],history_card_id=card_id,story_version=version,review_version=review_version,
            checklist=[{"criterion":criterion,"checked":False} for criterion in row["acceptance_criteria"]],
            observations="Pendiente de revisión funcional con Josué, Mario y los usuarios del área.",finished=False,
            solution_proposed=row["solution"],reviewed_by="Codex · implementación",created_at=now,
        ))


def downgrade():
    # Discovery history is append-only and remains available on code rollback.
    pass
