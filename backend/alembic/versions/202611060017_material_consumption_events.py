"""Backfill dated material-consumption audit events for project costing.

Revision ID: 202611060017
Revises: 202611060016
"""
from decimal import Decimal
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision = "202611060017"
down_revision = "202611060016"
branch_labels = None
depends_on = None

MIGRATION_ACTOR = "migration:material-consumption-audit"


def upgrade() -> None:
    bind = op.get_bind()
    movements = sa.Table("ae_inventory_movements", sa.MetaData(), autoload_with=bind)
    materials = sa.Table("ae_work_order_materials", sa.MetaData(), autoload_with=bind)
    lines = bind.execute(sa.select(materials.c.id, materials.c.installation_id, materials.c.item_id)).mappings().all()
    for line in lines:
        sources = bind.execute(sa.select(movements).where(
            movements.c.work_order_material_id == line["id"],
            movements.c.installation_id == line["installation_id"],
            movements.c.item_id == line["item_id"],
            movements.c.movement_type == "out",
        )).mappings().all()
        for source in sources:
            if bind.execute(sa.select(movements.c.id).where(
                movements.c.related_movement_id == source["id"],
                movements.c.movement_type == "consumption",
            ).limit(1)).first():
                continue
            if (source["reason"] or "").startswith("Orden "):
                continue
            returned = Decimal(str(bind.execute(sa.select(sa.func.coalesce(sa.func.sum(movements.c.quantity), 0)).where(
                movements.c.related_movement_id == source["id"], movements.c.movement_type == "return",
            )).scalar_one()))
            net_quantity = max(Decimal("0"), Decimal(str(source["quantity"])) - returned)
            if net_quantity <= 0:
                continue
            bind.execute(movements.insert().values(
                id=str(uuid4()),
                item_id=line["item_id"],
                installation_id=line["installation_id"],
                quantity=net_quantity,
                movement_type="consumption",
                related_movement_id=source["id"],
                work_order_material_id=line["id"],
                unit_cost=source["unit_cost"],
                reason=f"Consumo recuperado del historial · {(source['reason'] or '')}"[:180],
                created_by=MIGRATION_ACTOR,
                created_at=source["created_at"],
            ))


def downgrade() -> None:
    movements = sa.table("ae_inventory_movements", sa.column("created_by", sa.String()))
    op.execute(sa.delete(movements).where(movements.c.created_by == MIGRATION_ACTOR))
