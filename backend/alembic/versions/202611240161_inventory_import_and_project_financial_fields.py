"""Support legacy inventory imports and project source details.

Revision ID: 202611240161
Revises: 202611170160
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
from uuid import uuid4


revision = "202611240161"
down_revision = "202611170160"
branch_labels = None
depends_on = None


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    if column.name not in {row["name"] for row in sa.inspect(op.get_bind()).get_columns(table)}:
        op.add_column(table, column)


def _add_index_if_missing(table: str, name: str, columns: list[str], unique: bool = False) -> None:
    if name not in {row["name"] for row in sa.inspect(op.get_bind()).get_indexes(table)}:
        op.create_index(name, table, columns, unique=unique)


def _add_fk_if_missing(table: str, name: str, column: str, target: str, target_column: str) -> None:
    fks = sa.inspect(op.get_bind()).get_foreign_keys(table)
    if any(fk.get("name") == name or (fk.get("constrained_columns") == [column] and fk.get("referred_table") == target) for fk in fks):
        return
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table(table) as batch:
            batch.create_foreign_key(name, target, [column], [target_column], ondelete="RESTRICT")
    else:
        op.create_foreign_key(name, table, target, [column], [target_column], ondelete="RESTRICT")


def _record_inventory_history_card(bind) -> None:
    inspector = sa.inspect(bind)
    if not inspector.has_table("ae_history_cards") or not inspector.has_table("ae_history_card_reviews"):
        return
    cards = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    reviews = sa.Table("ae_history_card_reviews", sa.MetaData(), autoload_with=bind)
    story_id = "US-46"
    card = bind.execute(sa.select(cards).where(cards.c.story_id == story_id).order_by(cards.c.version.desc()).limit(1)).mappings().first()
    if card is None:
        now = datetime.now(timezone.utc)
        card_id = str(uuid4())
        bind.execute(cards.insert().values(
            id=card_id, story_id=story_id, version=1, iteration="Inventario · iteración 1",
            stakeholder="Stakeholder Arco Energy · autor por confirmar", requested_by="Usuario Arco Energy",
            source_literal=(
                "mira estas imagenes, analiza sus estados, sus modelos, sus campos necesarios, sus funcionalidades, y vamos a convertir todo el inventario en un modulo, documentalo en el storycard para despues implementar el modulo de inventario.\n\n"
                "mira ahora vamos a trabajar por modulos; entonces vas a agregar historycards que yo mismo fui agregando; entonces la siguiente storycard que necesito es que dentro del modulo de inventario dejes todas estas funcionalidades que ya tiene el sistema de inventario. [Image #1]\n\n"
                "exacto entonces haz la implementacion tomalo como un /goal no te detengas hasta que este terminado, ahora si ya vamos a implementar incrementalmente entonces ya vamos a ir haciendo modelos, checa con que relacion de otros modulos tiene, por ahora el modulo de usuarios que ya esta listo con roles y el de inventario, toma en cuenta los otros modulos que vamos a implementar.\n\n"
                "Para empezar las opciones de los modulos en el sidebar deben ser desplegables es decir cada modulo va a tener sus diferentes opciones. empecemos por inventario; actualmente las opciones de inventario que seria dashboard entradas salidas deben ir como opciones desplegables en el panel lateral. 2.- en downloads acabo de dejar un zip es el ultimo que descargue; internamente tiene un csv que necesito que extraigas y leas; despues ajustes todos los modelos e importes el data que ahi esta. tomalo como /goal"
            ),
            source_type="conversation", source_reference="Conversación Arco Energy · 24/11/2026 · nueve capturas de referencia",
            source_artifact={"type": "screenshots", "count": 9, "module": "inventario"}, source_language="es",
            source_attribution="Usuario del producto · nombre no registrado", source_occurred_at="2026-11-24",
            source_confidence="user_provided", source_links=[],
            normalized_story=(
                "Como usuario de Arco Energy, quiero conservar las funciones mostradas en las nueve capturas del módulo de inventario y acceder a sus secciones "
                "desde un submenú desplegable del sidebar del CRM; también quiero importar el catálogo, movimientos, proveedores y proyectos del último ZIP de exportación."
            ),
            acceptance_criteria=[
                "El sidebar del CRM despliega las opciones de Inventario: Dashboard, Catálogo, Entradas, Salidas, Kardex, Escáner, Reportes y Configuración.",
                "El inventario se muestra dentro del panel central del CRM y conserva la navegación y controles de la aplicación.",
                "El último ZIP con CSV se puede importar sin guardar los datos fuente en el repositorio y la importación se puede repetir sin duplicar movimientos.",
                "Los folios documentales admiten varios renglones de producto y el historial importado no vuelve a alterar el stock de la fotografía actual.",
                "Los modelos conservan las relaciones disponibles con categorías, proveedores, clientes, proyectos, artículos y responsables."
            ], unresolved_questions=["Revisar el resultado y los mínimos de stock con el stakeholder antes de marcar la historia como terminada."],
            linked_cards=["US-42", "US-45"], recorded_by="Codex · registro desde conversación", created_at=now,
        ))
        card = {"id": card_id, "version": 1}

    version = card["version"]
    already_reviewed = bind.execute(sa.select(reviews.c.id).where(
        reviews.c.story_id == story_id, reviews.c.story_version == version,
        reviews.c.solution_proposed.like("%CSV de inventario%"),
    ).limit(1)).first()
    if already_reviewed:
        return
    review_version = (bind.execute(sa.select(sa.func.max(reviews.c.review_version)).where(reviews.c.story_id == story_id)).scalar_one_or_none() or 0) + 1
    bind.execute(reviews.insert().values(
        id=str(uuid4()), story_id=story_id, history_card_id=card["id"], story_version=version,
        review_version=review_version,
        checklist=[{"criterion": criterion, "checked": False} for criterion in (card.get("acceptance_criteria") or [])],
        observations="Pendiente de revisión funcional y de mínimos de stock con el stakeholder.", finished=False,
        solution_proposed=(
            "Se agregó navegación desplegable de las secciones de inventario al sidebar principal del CRM; el módulo se mantiene en el panel central. "
            "Se ampliaron los modelos para proyectos y movimientos con folios compartidos e identificadores de importación idempotente. "
            "Se agregó un importador de ZIP/CSV externo al repositorio para importar el catálogo de existencias, entradas, salidas, proveedores y proyectos; "
            "los movimientos históricos no cambian nuevamente el stock actual. La ejecución DEV y la verificación de los datos importados quedan como paso de despliegue."
        ), reviewed_by="Codex · Implementación", created_at=datetime.now(timezone.utc),
    ))


def upgrade() -> None:
    bind = op.get_bind()

    for column in (
        sa.Column("location", sa.String(240), nullable=False, server_default=""),
        sa.Column("status", sa.String(40), nullable=False, server_default="planning"),
        sa.Column("source_status", sa.String(80), nullable=False, server_default=""),
        sa.Column("priority", sa.String(30), nullable=False, server_default="medium"),
        sa.Column("progress_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("contract_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("source", sa.String(40), nullable=False, server_default="crm"),
    ):
        _add_column_if_missing("ae_projects", column)

    _add_column_if_missing("ae_inventory_movements", sa.Column("source_key", sa.String(64), nullable=True))
    _add_column_if_missing("ae_inventory_movements", sa.Column("project_id", sa.String(36), nullable=True))

    # Folios identify a receipt or dispatch document, which may contain multiple items.
    for index in sa.inspect(bind).get_indexes("ae_inventory_movements"):
        if index["column_names"] == ["folio"] and index.get("unique"):
            op.drop_index(index["name"], table_name="ae_inventory_movements")
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_folio", ["folio"])
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_source_key", ["source_key"], unique=True)
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_project_id", ["project_id"])
    _add_fk_if_missing("ae_inventory_movements", "fk_ae_inventory_movement_project", "project_id", "ae_projects", "id")

    if not sa.inspect(bind).has_table("ae_inventory_import_batches"):
        op.create_table(
            "ae_inventory_import_batches",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("source_sha256", sa.String(64), nullable=False),
            sa.Column("source_filename", sa.String(255), nullable=False),
            sa.Column("summary", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("imported_by", sa.String(180), nullable=False, server_default=""),
            sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False),
        )
    _add_index_if_missing("ae_inventory_import_batches", "ix_ae_inventory_import_batches_source_sha256", ["source_sha256"], unique=True)
    _record_inventory_history_card(bind)


def downgrade() -> None:
    # Preserve imported ledger/project data; rollback only removes this migration marker.
    pass
