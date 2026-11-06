"""Remove only the known zero-value ArcoEnergy demonstration seed rows.

Revision ID: 202611060002
Revises: 202611060001
"""
from alembic import op
from sqlalchemy import delete, select
from app.models import InventoryItem, InventoryMovement, QuotePackage

revision = "202611060002"
down_revision = "202611060001"
branch_labels = None
depends_on = None

SEED_NAMES = (
    "Panel solar Jinko 610 W", "Inversor Growatt 3 kW", "Inversor Growatt 5 kW",
    "Inversor Huawei 6 kW", "Inversor Huawei 10 kW", "Riel de aluminio",
    "Abrazadera intermedia", "Abrazadera final", "Anclaje para techo",
    "Cable solar 6 mm rojo", "Cable solar 6 mm negro", "Conector MC4",
    "Interruptor termomagnético DC", "Interruptor termomagnético AC",
    "Cable de puesta a tierra",
)


def upgrade() -> None:
    bind = op.get_bind()
    # Verified DEV contents were all provisional packages with no quote history.
    bind.execute(delete(QuotePackage).where(QuotePackage.is_demo.is_(True)))
    # Keep any item that acquired stock, a cost, a minimum, or movement history.
    used = select(InventoryMovement.item_id).where(InventoryMovement.item_id == InventoryItem.id).exists()
    bind.execute(delete(InventoryItem).where(
        InventoryItem.name.in_(SEED_NAMES), InventoryItem.quantity == 0,
        InventoryItem.minimum_quantity == 0, InventoryItem.unit_cost == 0,
        ~used,
    ))


def downgrade() -> None:
    # Fixture data is intentionally not restored on rollback.
    pass
