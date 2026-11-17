"""Register the detailed inventory module reference as US-45.

Revision ID: 202611170159
Revises: 202611170158
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611170159"
down_revision = "202611170158"
branch_labels = None
depends_on = None

ITERATION = "Iteración 157 · alcance integral del módulo de inventario · 2026-11-17"
SOURCE_LITERAL = "mira estas imagenes, analiza sus estados, sus modelos, sus campos necesarios, sus funcionalidades, y vamos a convertir todo el inventario en un modulo, documentalo en el storycard para despues implementar el modulo de inventario"
SOURCE_DOC = "docs/discovery/sources/inventory-module-detail.md"
NORMALIZED_STORY = (
    "Como responsable de Arco Energy, quiero que el inventario funcione como un módulo integrado para administrar "
    "productos, existencias, entradas, salidas, kardex, escaneo, reportes, proveedores, proyectos y configuración, "
    "con trazabilidad entre movimientos y sus documentos de origen."
)
ACCEPTANCE_CRITERIA = (
    "El catálogo permite consultar y buscar productos por nombre, código o código de barras, filtrar por categoría y estado, y consultar imágenes, subcategorías, existencia, nivel de stock, costo, unidad y ubicación.",
    "El catálogo permite registrar un producto y actualizar sus datos; el estado activo/inactivo y los niveles OK/bajo/agotado se distinguen claramente. La existencia se puede rastrear a movimientos de almacén.",
    "Una entrada registra folio, producto, cantidad positiva, proveedor cuando aplique, factura, responsable y fecha; la búsqueda permite localizar el movimiento por folio o producto.",
    "Una salida registra folio, producto, cantidad negativa, proyecto cuando aplique, departamento, responsable y fecha; una devolución se registra como movimiento vinculado y auditable.",
    "El kardex presenta, para el producto seleccionado, los movimientos ordenados con su tipo, folio/origen, cantidad, fecha, responsable y saldo resultante.",
    "El escáner admite cámara y captura manual; al reconocer un código permite seleccionar una acción de inventario y confirma el producto antes de guardar el movimiento.",
    "Los reportes aceptan un período y alcance seleccionables, muestran totales de productos, stock bajo, agotados y valor, distribución por categoría, productos con más salidas e inventario general, y permiten generar/descargar el reporte mensual.",
    "El directorio de proveedores muestra nombre, contacto, correo, teléfono y RFC, permite búsqueda y alta/edición, y conserva el historial de movimientos aunque cambie el proveedor.",
    "El seguimiento de proyectos muestra folio, proyecto/instalación, cliente, estado, prioridad, avance, responsable, fecha y resumen económico de monto, materiales, gastos y utilidad; permite registrar gastos de instalación vinculados al proyecto.",
    "Configuración administra categorías y descripciones y ofrece una sección de datos de empresa.",
    "El dashboard enlaza productos, entradas, salidas, alertas, reportes y movimientos recientes con las mismas fuentes persistentes, y los permisos limitan cada acción por rol.",
    "Los movimientos que afectan existencias conservan vínculo con la compra, orden de trabajo, proyecto o documento de origen; las correcciones y devoluciones mantienen bitácora y trazabilidad, sin borrar movimientos contabilizados.",
)
UNRESOLVED_QUESTIONS = (
    "Confirmar campos obligatorios y opcionales de producto, entrada, salida, proveedor, proyecto y empresa; distinguir campos visibles de los que deben añadirse al formulario.",
    "Aprobar unidades, ubicaciones, subcategorías, mínimos/máximos y la fórmula de costo/valuación (promedio, PEPS u otra), redondeo y moneda.",
    "Definir si se permiten existencias negativas, cómo se autorizan ajustes/mermas, y cómo se corrigen o revierten movimientos ya vinculados a compras, ventas, proveedores y órdenes de trabajo.",
    "Definir el folio por tipo de movimiento, la relación de compras con proveedor y cuentas por pagar/caja/banco, y la relación de salidas con venta, orden de trabajo, proyecto y costo directo.",
    "Acordar reglas de devolución parcial/total, merma, material dañado, entrega y recepción de materiales, y conciliación de saldos del kardex.",
    "Confirmar estados y transiciones permitidos de producto, movimiento y proyecto; quién puede registrar, autorizar, cancelar, devolver y consultar costos por cada rol.",
    "Definir las columnas y formatos de exportación PDF, período de corte, filtros de reportes y tratamiento de movimientos anulados/revertidos.",
    "Validar el significado de todos los importes, contadores y ejemplos de folios visibles en las capturas; son datos de referencia y no parámetros aprobados.",
    "Confirmar integración con Drive, política de adjuntos/facturas, retención, permisos de cámara y comportamiento offline del escáner PWA.",
    "El autor nominal del mensaje no está identificado; mantener requested_by como 'Por identificar' hasta confirmación.",
)
LINKED_CARDS = ["US-19", "US-20", "US-26", "US-27", "US-28", "US-29", "US-30", "US-32", "US-36", "US-38", "US-44"]
IMAGES = [
    ("01-products.png", "f31b88f5a4ba3853c3cafc5fbf85f18e2b99bce24d561ebc269dbe5646637dab", "Catálogo agrupado por categoría: búsqueda, filtros, exportar PDF, alta, código, imagen, producto, subcategoría, stock, nivel, costo, ubicación, estatus y acciones."),
    ("02-entries.png", "90f5a73a4462cd2c5978decae6ea65eb5a054b9af1ae1a503ba207e4a71a15cc", "Entradas: folio, producto, cantidad, proveedor, factura, responsable, fecha; búsqueda y alta."),
    ("03-exits.png", "5166f59eafba5fad0c1f36ee631a4a1064046e7fa5317cd01eda6ffb2efee66b", "Salidas: folio, producto, cantidad, proyecto, departamento, responsable, fecha y acción de devolución."),
    ("04-kardex.png", "969e6e512751877b74405b7604014f2f9e5d9183e73d9d37952e2be52d257676", "Kardex por producto seleccionado; historial de movimientos."),
    ("05-scanner.png", "29ca2620e522b31c37a06c71960516e759eadbae9e9dba5659e16a47ac5c13b7", "Escáner de productos: modos cámara/manual, permiso de cámara, detección automática y selección de acción."),
    ("06-reports.png", "c2e13b21b16e19ab0c100d830bc1669a8d7260c2988b272c88c873a36e67501b", "Reportes: período, reporte mensual, alcance, indicadores, distribución por categoría, top salidas e inventario general."),
    ("07-suppliers.png", "62f2dc2a33dbff70c3e28571540ebd6ecca806dc11be1132131b7b6f42ffcd3f", "Proveedores: nombre, contacto, email, teléfono y RFC; búsqueda, alta y acciones."),
    ("08-projects.png", "a329230002cbf6dc67509b6d081133d8633a39653405c317f4dba9a6914a3510", "Proyectos: folio, instalación/proyecto, cliente, estado, prioridad, avance, responsable, fecha y resumen económico; agenda, alta y gasto de instalación."),
    ("09-settings.png", "6f8562e41d4459e816b4e1696fff89ab87769d344d1fef03e71ee89b3c22bdad", "Configuración: categorías de producto con descripción y pestaña de empresa."),
]


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("ae_history_cards"):
        return
    history = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    exists = bind.execute(sa.select(history.c.id).where(history.c.story_id == "US-45").limit(1)).first()
    if exists:
        return
    artifacts = [{
        "artifact_type": "mensaje de conversación",
        "reference": "Chat del proyecto Arco Energy · alcance detallado del módulo de inventario",
        "channel": "ChatGPT",
        "location": "Mensaje del usuario del 2026-11-17",
        "sha256": None,
    }]
    links = [{"artifact_index": 0, "relation": "literal", "location": "Solicitud literal de US-45"}]
    for filename, sha256, description in IMAGES:
        path = f"docs/discovery/sources/inventory-module-detail/{filename}"
        index = len(artifacts)
        artifacts.append({
            "artifact_type": "captura de pantalla de referencia",
            "reference": path,
            "channel": "Imagen compartida por el usuario",
            "location": description,
            "sha256": sha256,
        })
        links.append({"artifact_index": index, "relation": "inference", "location": description})
    bind.execute(history.insert().values(
        id=str(uuid4()), story_id="US-45", version=1, iteration=ITERATION,
        stakeholder="Equipo Arco Energy", requested_by="Por identificar",
        source_literal=SOURCE_LITERAL, source_type="Conversación e imágenes",
        source_reference=f"{SOURCE_DOC} · docs/discovery/sources/inventory-module-detail/",
        source_artifact={"artifacts": artifacts}, source_language="es",
        source_attribution="Usuario Arco Energy (autor nominal por identificar)",
        source_occurred_at="2026-11-17", source_confidence="needs_validation",
        source_links=links, normalized_story=NORMALIZED_STORY,
        acceptance_criteria=list(ACCEPTANCE_CRITERIA),
        unresolved_questions=list(UNRESOLVED_QUESTIONS), linked_cards=LINKED_CARDS,
        recorded_by="system:discovery-iteration-157", created_at=datetime.now(timezone.utc),
    ))


def downgrade() -> None:
    # Story cards are append-only discovery records and remain on rollback.
    pass
