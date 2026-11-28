"""Record follow-up CRM presentation requests as append-only history cards.

Revision ID: 202611280165
Revises: 202611280164
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611280165"
down_revision = "202611280164"
branch_labels = None
depends_on = None

CARDS = [
    {
        "story_id": "US-59",
        "iteration": "CRM · Directorio con tarjetas responsivas",
        "source_literal": "si me gusto solo dale mas formato a las tarjetas mas separacion; [Image #1] y que no se salgan los containers todo debe quedar bien responsivo con sus containers auto etc.",
        "normalized_story": "Como usuario del CRM, quiero tarjetas de clientes con separación suficiente y altura adaptable para consultar todos sus datos sin que se desborden o se encimen.",
        "acceptance_criteria": ["La cuadrícula mantiene separación clara entre tarjetas.", "Cada tarjeta crece según el contenido y no invade otra fila.", "La cuadrícula se adapta a pantallas pequeñas sin desbordamiento horizontal."],
        "solution": "Se eliminó la proporción fija de tarjeta, se permitió envolver contenido largo y se ajustaron columnas, alturas y espacios para pantallas responsivas.",
    },
    {
        "story_id": "US-60",
        "iteration": "CRM · Resumen inicial centrado en ventas",
        "source_literal": "el dashboard vamos a modificarlo todo; primero que nada quita todo del dashboard yo te voy a ir diciendo que secciones vamos a agregar. [Image #1] para empezar primero necesitamos el de ventas; es decir que se ha vendido este mes. deben ir por contenedores horizontales y grandes, porque despues tambien vamos a tener el container de cotizaciones el de cuentas por cobrar y el de operaciones. van a tener tarjetas e indicadores grandes.",
        "normalized_story": "Como administrador, quiero que el Resumen muestre inicialmente solo un contenedor amplio de ventas del mes con indicadores grandes, para ir incorporando los demás bloques por iteraciones posteriores.",
        "acceptance_criteria": ["El Resumen presenta solo el bloque de ventas de este mes.", "El importe mensual es visible como indicador principal.", "Se muestran indicadores de operaciones, contado y crédito.", "El bloque ocupa el ancho disponible y responde a pantallas pequeñas."],
        "solution": "Se sustituyeron los paneles existentes por un contenedor horizontal que calcula ventas del mes y muestra importe, operaciones, contado y crédito.",
    },
    {
        "story_id": "US-61",
        "iteration": "CRM · Instalaciones con tablero de muestra",
        "source_literal": "al apartado de instalaciones agregale porfavor mockup data. [Image #1] unas 10 porfavor. quita todos los encabezados simplemente deja la palabra instalaciones en grande hasta arriba",
        "normalized_story": "Como coordinador, quiero ver alrededor de diez órdenes ficticias en el tablero de Instalaciones y dejar como único encabezado el título grande, para previsualizar el flujo por etapas.",
        "acceptance_criteria": ["Los datos de muestra son solo de DEV, identificables como DEMO y sembrados de forma idempotente.", "El tablero presenta aproximadamente diez órdenes en Pendientes, En progreso y Terminadas.", "El encabezado visible de la página conserva únicamente el título Instalaciones.", "La acción para asignar una instalación continúa disponible para usuarios autorizados."],
        "solution": "Se añadieron siete órdenes DEMO estables a la siembra de DEV para completar diez y se simplificó el encabezado conservando la acción de asignación.",
    },
    {
        "story_id": "US-62",
        "iteration": "CRM · Ventas en tabla",
        "source_literal": "en el modulo de ventas esta tarjeta mejor cambiala a tabla porfavor",
        "normalized_story": "Como usuario de Ventas, quiero consultar las operaciones en una tabla para comparar folios, clientes, método, orden, materiales e importes con rapidez.",
        "acceptance_criteria": ["Las ventas registradas se muestran en filas y columnas.", "La tabla presenta folio, cliente, tipo, proyecto/orden, cuadrilla/fecha, materiales, total, cobro y acciones.", "La tabla conserva desplazamiento horizontal en pantallas pequeñas."],
        "solution": "Se reemplazaron las tarjetas por una tabla de operaciones con columnas contables y operativas, acciones de corrección y desplazamiento horizontal.",
    },
    {
        "story_id": "US-63",
        "iteration": "CRM · Modal de operaciones y espaciado de tablas",
        "source_literal": "este modal que describe las operaciones hazlo bien amplio, ademas agrega paddings a las tablas para que no se vean hasta la orilla del container",
        "normalized_story": "Como usuario que registra operaciones, quiero un modal amplio y tablas con margen interior para leer y capturar información con comodidad.",
        "acceptance_criteria": ["Los modales amplios aprovechan mejor el ancho disponible.", "Las tablas mantienen espacio respecto al borde de su contenedor.", "El modal y las tablas siguen siendo utilizables en pantallas pequeñas."],
        "solution": "Se amplió el ancho máximo de modales de operación y se agregaron márgenes interiores a tablas en tarjetas y modales.",
    },
    {
        "story_id": "US-64",
        "iteration": "CRM · Calendario de cobranza antes de las tarjetas",
        "source_literal": "en el de cobranza mejor si pon las tarjetas de los clientes abajo y el calendario hasta arriba",
        "normalized_story": "Como persona de cobranza, quiero ver primero el calendario y debajo las tarjetas de clientes con saldo pendiente.",
        "acceptance_criteria": ["El calendario de cobranza aparece encima de las tarjetas.", "Las tarjetas mantienen saldos y acciones por cliente.", "El calendario conserva el resaltado de hoy y los nombres de clientes con vencimiento."],
        "solution": "Se colocó el calendario como primera sección del módulo de Cobranza y se movió la cartera en tarjetas debajo, conservando los previews por fecha y el resaltado de hoy.",
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
        version = (bind.execute(sa.select(sa.func.max(cards.c.version)).where(
            cards.c.story_id == row["story_id"],
        )).scalar_one_or_none() or 0) + 1
        card_id = str(uuid4())
        bind.execute(cards.insert().values(
            id=card_id, version=version, source_type="conversation", source_language="es",
            source_artifact={"type": "conversation", "captured_as": "literal", "reference": "Conversación Arco Energy · Iteración CRM · 28/11/2026"},
            source_attribution="Usuario Arco Energy · autor por confirmar", source_confidence="direct_quote", source_links=[],
            unresolved_questions=[], linked_cards=[], recorded_by="Codex · implementación", created_at=now,
            source_reference="Conversación Arco Energy · Iteración CRM · 28/11/2026",
            acceptance_criteria=row["acceptance_criteria"], source_literal=row["source_literal"],
            normalized_story=row["normalized_story"], stakeholder="Stakeholder Arco Energy · autor por confirmar",
            requested_by="Usuario Arco Energy · autor por confirmar", iteration=row["iteration"],
        ))
        review_version = (bind.execute(sa.select(sa.func.max(reviews.c.review_version)).where(
            reviews.c.story_id == row["story_id"],
        )).scalar_one_or_none() or 0) + 1
        bind.execute(reviews.insert().values(
            id=str(uuid4()), story_id=row["story_id"], history_card_id=card_id,
            story_version=version, review_version=review_version,
            checklist=[{"criterion": criterion, "checked": False} for criterion in row["acceptance_criteria"]],
            observations="Pendiente de validación con usuarios de Arco Energy.", finished=False,
            solution_proposed=row["solution"], reviewed_by="Codex · implementación", created_at=now,
        ))


def downgrade():
    # Discovery history is append-only and remains available on code rollback.
    pass
