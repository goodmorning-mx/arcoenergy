"""Reserve sale materials for work orders and track confirmed use.

Revision ID: 202611060015
Revises: 202611060014
"""
from alembic import op
import sqlalchemy as sa
from decimal import Decimal
from uuid import uuid4

revision = "202611060015"
down_revision = "202611060014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import WorkOrderMaterial

    bind = op.get_bind()
    WorkOrderMaterial.__table__.create(bind=bind, checkfirst=True)
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_inventory_movements")}
    if "work_order_material_id" not in columns:
        with op.batch_alter_table("ae_inventory_movements") as batch:
            batch.add_column(sa.Column("work_order_material_id", sa.String(36), nullable=True))
            batch.create_foreign_key(
                "fk_ae_inventory_movements_work_order_material_id_ae_work_order_materials",
                "ae_work_order_materials", ["work_order_material_id"], ["id"],
            )
            batch.create_index("ix_ae_inventory_movements_work_order_material_id", ["work_order_material_id"])

    sales = sa.Table("ae_sales", sa.MetaData(), autoload_with=bind)
    installations = sa.Table("ae_installations", sa.MetaData(), autoload_with=bind)
    movements = sa.Table("ae_inventory_movements", sa.MetaData(), autoload_with=bind)
    items = sa.Table("ae_inventory", sa.MetaData(), autoload_with=bind)
    existing = {row[0] for row in bind.execute(sa.select(WorkOrderMaterial.__table__.c.installation_id))}
    for sale in bind.execute(sa.select(sales.c.id, sales.c.folio, sales.c.installation_id)).mappings():
        if sale["installation_id"] in existing:
            continue
        installation = bind.execute(sa.select(installations.c.folio).where(installations.c.id == sale["installation_id"])).first()
        if not installation:
            continue
        direct_reason = f"Orden {installation.folio} · Venta {sale['folio']}"
        issues = bind.execute(sa.select(movements).where(
            movements.c.installation_id == sale["installation_id"],
            movements.c.movement_type == "out",
            movements.c.reason == direct_reason,
        )).mappings().all()
        grouped: dict[str, list] = {}
        for issue in issues:
            grouped.setdefault(issue["item_id"], []).append(issue)
        for item_id, sale_issues in grouped.items():
            issue_ids = [row["id"] for row in sale_issues]
            returned_to_sale = Decimal(str(bind.execute(sa.select(sa.func.coalesce(sa.func.sum(movements.c.quantity), 0)).where(
                movements.c.related_movement_id.in_(issue_ids), movements.c.movement_type == "return",
            )).scalar_one()))
            requested = sum((Decimal(str(row["quantity"])) for row in sale_issues), Decimal("0"))
            preissued = max(Decimal("0"), requested - returned_to_sale)
            other_issues = bind.execute(sa.select(movements).where(
                movements.c.installation_id == sale["installation_id"],
                movements.c.item_id == item_id,
                movements.c.movement_type == "out",
                movements.c.reason != direct_reason,
            )).mappings().all()
            other_net = Decimal("0")
            for source in other_issues:
                returned = Decimal(str(bind.execute(sa.select(sa.func.coalesce(sa.func.sum(movements.c.quantity), 0)).where(
                    movements.c.related_movement_id == source["id"], movements.c.movement_type == "return",
                )).scalar_one()))
                other_net += max(Decimal("0"), Decimal(str(source["quantity"])) - returned)
            # Previous releases deducted sale issues and the installer's confirmation
            # separately. Restore the overlapping physical deduction once, preserving
            # the original audit rows and adding linked return rows for traceability.
            duplicated = min(preissued, other_net)
            consumed = min(preissued, other_net)
            item = bind.execute(sa.select(items.c.quantity).where(items.c.id == item_id)).first()
            if item and duplicated:
                bind.execute(sa.update(items).where(items.c.id == item_id).values(quantity=items.c.quantity + duplicated))
            material_id = str(uuid4())
            item_row = bind.execute(sa.select(items.c.unit_cost).where(items.c.id == item_id)).first()
            bind.execute(WorkOrderMaterial.__table__.insert().values(
                id=material_id, installation_id=sale["installation_id"], item_id=item_id,
                requested_quantity=requested, preissued_quantity=preissued,
                consumed_quantity=consumed, unit_cost=item_row[0] if item_row else 0,
                created_by="migration:work-order-materials",
            ))
            bind.execute(sa.update(movements).where(movements.c.id.in_(issue_ids)).values(work_order_material_id=material_id))
            if other_issues:
                other_ids = [row["id"] for row in other_issues]
                bind.execute(sa.update(movements).where(movements.c.id.in_(other_ids)).values(work_order_material_id=material_id))
                bind.execute(sa.update(movements).where(movements.c.related_movement_id.in_(other_ids)).values(work_order_material_id=material_id))
            remaining_restore = duplicated
            for source in other_issues:
                if remaining_restore <= 0:
                    break
                returned = Decimal(str(bind.execute(sa.select(sa.func.coalesce(sa.func.sum(movements.c.quantity), 0)).where(
                    movements.c.related_movement_id == source["id"], movements.c.movement_type == "return",
                )).scalar_one()))
                restorable = min(remaining_restore, max(Decimal("0"), Decimal(str(source["quantity"])) - returned))
                if restorable <= 0:
                    continue
                bind.execute(movements.insert().values(
                id=str(uuid4()), item_id=item_id,
                    installation_id=sale["installation_id"], related_movement_id=source["id"],
                    work_order_material_id=material_id, quantity=restorable, movement_type="return",
                    unit_cost=source["unit_cost"], reason="Corrección de doble descuento previo a reserva de orden",
                    created_by="migration:work-order-materials",
                ))
                remaining_restore -= restorable


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("ae_inventory_movements")}
    if "work_order_material_id" in columns:
        with op.batch_alter_table("ae_inventory_movements") as batch:
            batch.drop_index("ix_ae_inventory_movements_work_order_material_id")
            batch.drop_constraint("fk_ae_inventory_movements_work_order_material_id_ae_work_order_materials", type_="foreignkey")
            batch.drop_column("work_order_material_id")
    op.drop_table("ae_work_order_materials")
