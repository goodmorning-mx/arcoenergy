"""Add normalized inventory categories, catalog metadata and movement references.

Revision ID: 202611170160
Revises: 202611170159
"""
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "202611170160"
down_revision = "202611170159"
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    columns = {row["name"] for row in sa.inspect(op.get_bind()).get_columns(table_name)}
    if column.name not in columns:
        op.add_column(table_name, column)


def _add_index_if_missing(table_name: str, name: str, columns: list[str], *, unique: bool = False) -> None:
    indexes = {row["name"] for row in sa.inspect(op.get_bind()).get_indexes(table_name)}
    if name not in indexes:
        op.create_index(name, table_name, columns, unique=unique)


def _add_fk_if_missing(table_name: str, name: str, columns: list[str], referred_table: str, referred_columns: list[str]) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if any(
        fk.get("name") == name or (
            fk.get("constrained_columns") == columns
            and fk.get("referred_table") == referred_table
            and fk.get("referred_columns") == referred_columns
        )
        for fk in inspector.get_foreign_keys(table_name)
    ):
        return
    local = ", ".join(columns)
    remote = ", ".join(referred_columns)
    orphan = bind.execute(sa.text(
        f"SELECT COUNT(*) FROM {table_name} child LEFT JOIN {referred_table} parent "
        f"ON child.{columns[0]} = parent.{referred_columns[0]} "
        f"WHERE child.{columns[0]} IS NOT NULL AND parent.{referred_columns[0]} IS NULL"
    )).scalar_one()
    if orphan:
        raise RuntimeError(f"Cannot add {name}: {orphan} orphan {table_name}.{local} references to {referred_table}.{remote}.")
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch:
            batch.create_foreign_key(name, referred_table, columns, referred_columns, ondelete="RESTRICT")
    else:
        op.create_foreign_key(name, table_name, referred_table, columns, referred_columns, ondelete="RESTRICT")


def _set_not_null(table_name: str, column_name: str) -> None:
    column = next(row for row in sa.inspect(op.get_bind()).get_columns(table_name) if row["name"] == column_name)
    if not column["nullable"]:
        return
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table(table_name) as batch:
            batch.alter_column(column_name, existing_type=column["type"], nullable=False)
    else:
        op.alter_column(table_name, column_name, existing_type=column["type"], nullable=False)


def _record_story_solution(bind) -> None:
    inspector = sa.inspect(bind)
    if not inspector.has_table("ae_history_cards") or not inspector.has_table("ae_history_card_reviews"):
        return
    cards = sa.Table("ae_history_cards", sa.MetaData(), autoload_with=bind)
    reviews = sa.Table("ae_history_card_reviews", sa.MetaData(), autoload_with=bind)
    card = bind.execute(
        sa.select(cards).where(cards.c.story_id == "US-45").order_by(cards.c.version.desc()).limit(1)
    ).mappings().first()
    if card is None:
        return
    already_recorded = bind.execute(sa.select(reviews.c.id).where(
        reviews.c.story_id == "US-45", reviews.c.story_version == card["version"],
        reviews.c.solution_proposed.like("%iteración 160%"),
    ).limit(1)).first()
    if already_recorded:
        return
    review_version = (bind.execute(sa.select(sa.func.max(reviews.c.review_version)).where(reviews.c.story_id == "US-45")).scalar_one_or_none() or 0) + 1
    criteria = card["acceptance_criteria"] or []
    if isinstance(criteria, str):
        import json
        criteria = json.loads(criteria)
    bind.execute(reviews.insert().values(
        id=str(uuid4()), story_id="US-45", history_card_id=card["id"], story_version=card["version"],
        review_version=review_version,
        checklist=[{"criterion": criterion, "checked": False} for criterion in criteria],
        observations="Nota interna de implementación. Sin aceptación de stakeholder; Finished permanece pendiente.",
        finished=False,
        solution_proposed=(
            "Iteración 160 · módulo interno CRM de inventario: se agregaron categorías persistentes, código de producto, "
            "folios y relaciones de movimientos con artículo, proveedor/factura, instalación, compra y material de orden; API de búsqueda, "
            "reportes y permisos; pantallas de dashboard, catálogo, entradas, salidas/devoluciones, kardex, escáner, "
            "reportes y configuración de categorías con navegación propia basada en las capturas. Proveedores, proyectos "
            "y usuarios reutilizan sus portales existentes. Pruebas backend específicas y build del CRM aprobados; "
            "revisión funcional, contable y de umbrales por stakeholders pendiente."
        ),
        reviewed_by="Codex · Implementación v1", created_at=datetime.now(timezone.utc),
    ))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("ae_inventory_categories"):
        op.create_table(
            "ae_inventory_categories",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("name_key", sa.String(120), nullable=False, unique=True),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.String(180), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    _add_column_if_missing("ae_inventory", sa.Column("code", sa.String(64), nullable=True))
    _add_column_if_missing("ae_inventory", sa.Column("category_id", sa.String(36), nullable=True))
    _add_column_if_missing("ae_inventory", sa.Column("image_url", sa.Text(), nullable=False, server_default=""))
    _add_column_if_missing("ae_inventory", sa.Column("location", sa.String(120), nullable=False, server_default=""))
    _add_column_if_missing("ae_inventory", sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    _add_column_if_missing("ae_suppliers", sa.Column("contact_name", sa.String(180), nullable=False, server_default=""))
    _add_column_if_missing("ae_inventory_movements", sa.Column("folio", sa.String(40), nullable=True))
    _add_column_if_missing("ae_inventory_movements", sa.Column("source_type", sa.String(24), nullable=False, server_default="manual"))
    _add_column_if_missing("ae_inventory_movements", sa.Column("source_reference", sa.String(180), nullable=False, server_default=""))
    _add_column_if_missing("ae_inventory_movements", sa.Column("department", sa.String(100), nullable=False, server_default=""))
    _add_column_if_missing("ae_inventory_movements", sa.Column("supplier_id", sa.String(36), nullable=True))
    _add_column_if_missing("ae_inventory_movements", sa.Column("invoice_reference", sa.String(100), nullable=False, server_default=""))

    inventory = sa.Table("ae_inventory", sa.MetaData(), autoload_with=bind)
    category_table = sa.Table("ae_inventory_categories", sa.MetaData(), autoload_with=bind)
    items = bind.execute(sa.select(inventory.c.id, inventory.c.category, inventory.c.code, inventory.c.category_id)).mappings().all()
    categories_by_key: dict[str, str] = {}
    for item in items:
        name = (item["category"] or "").strip()
        if not name:
            continue
        key = " ".join(name.casefold().split())
        category_id = categories_by_key.get(key)
        if category_id is None:
            existing = bind.execute(sa.select(category_table.c.id).where(category_table.c.name_key == key).limit(1)).scalar_one_or_none()
            category_id = existing or str(uuid4())
            if existing is None:
                bind.execute(category_table.insert().values(
                    id=category_id, name=name[:100], name_key=key[:120], description="",
                    active=True, created_by="migration:inventory-category-backfill",
                    created_at=datetime.now(timezone.utc),
                ))
            categories_by_key[key] = category_id
        updates = {"category_id": category_id}
        if not item["code"]:
            updates["code"] = f"AE-{item['id'].replace('-', '')[:10].upper()}"
        bind.execute(inventory.update().where(inventory.c.id == item["id"]).values(**updates))
    # Assign a stable code even to uncategorized legacy records.
    for item in bind.execute(sa.select(inventory.c.id, inventory.c.code).where(inventory.c.code.is_(None))).mappings():
        bind.execute(inventory.update().where(inventory.c.id == item["id"]).values(code=f"AE-{item['id'].replace('-', '')[:10].upper()}"))

    movements = sa.Table("ae_inventory_movements", sa.MetaData(), autoload_with=bind)
    movement_rows = bind.execute(sa.select(
        movements.c.id, movements.c.movement_type, movements.c.created_at, movements.c.folio,
        movements.c.source_type, movements.c.source_reference, movements.c.reason,
        movements.c.purchase_line_id, movements.c.work_order_material_id, movements.c.installation_id,
    )).mappings().all()
    prefixes = {"in": "ENT", "purchase": "ENT", "out": "SAL", "return": "DEV", "damage": "MER", "waste": "MER", "receipt_reversal": "COR", "purchase_reversal": "COR", "consumption": "CON", "consumption_return": "COR"}
    for row in movement_rows:
        created = row["created_at"]
        if hasattr(created, "strftime"):
            day = created.strftime("%y%m%d")
        else:
            day = str(created or "00000000")[:10].replace("-", "")[2:]
        movement_type = row["movement_type"] or "in"
        prefix = prefixes.get(movement_type, "MOV")
        values = {}
        if not row["folio"]:
            values["folio"] = f"{prefix}-{day}-{row['id'].replace('-', '')[:8].upper()}"
        if not row["source_type"] or row["source_type"] == "manual":
            values["source_type"] = "purchase" if row["purchase_line_id"] else "work_order" if row["work_order_material_id"] or row["installation_id"] else "manual"
        if not row["source_reference"]:
            values["source_reference"] = (row["reason"] or "")[:180]
        if values:
            bind.execute(movements.update().where(movements.c.id == row["id"]).values(**values))

    _set_not_null("ae_inventory", "code")
    _set_not_null("ae_inventory_movements", "folio")

    _add_index_if_missing("ae_inventory_categories", "ix_ae_inventory_categories_name_key", ["name_key"])
    _add_index_if_missing("ae_inventory", "ix_ae_inventory_code", ["code"], unique=True)
    _add_index_if_missing("ae_inventory", "ix_ae_inventory_category_id", ["category_id"])
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_folio", ["folio"], unique=True)
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_item_id", ["item_id"])
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_installation_id", ["installation_id"])
    _add_index_if_missing("ae_inventory_movements", "ix_ae_inventory_movements_supplier_id", ["supplier_id"])
    _add_fk_if_missing("ae_inventory", "fk_ae_inventory_category", ["category_id"], "ae_inventory_categories", ["id"])
    _add_fk_if_missing("ae_inventory_movements", "fk_ae_inventory_movement_item", ["item_id"], "ae_inventory", ["id"])
    _add_fk_if_missing("ae_inventory_movements", "fk_ae_inventory_movement_installation", ["installation_id"], "ae_installations", ["id"])
    _add_fk_if_missing("ae_inventory_movements", "fk_ae_inventory_movement_related", ["related_movement_id"], "ae_inventory_movements", ["id"])
    _add_fk_if_missing("ae_inventory_movements", "fk_ae_inventory_movement_supplier", ["supplier_id"], "ae_suppliers", ["id"])
    _record_story_solution(bind)


def downgrade() -> None:
    # Keep ledger references and inventory catalog metadata on rollback.
    pass
