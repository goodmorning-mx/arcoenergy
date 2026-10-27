from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import InventoryItem
from app.product_api import SessionLocal


DEMO_STOCK_CATALOG = [
    ("Panel solar Jinko 610 W", "pieza"),
    ("Inversor Growatt 3 kW", "pieza"),
    ("Inversor Growatt 5 kW", "pieza"),
    ("Inversor Huawei 6 kW", "pieza"),
    ("Inversor Huawei 10 kW", "pieza"),
    ("Riel de aluminio", "pieza"),
    ("Abrazadera intermedia", "pieza"),
    ("Abrazadera final", "pieza"),
    ("Anclaje para techo", "pieza"),
    ("Cable solar 6 mm rojo", "metro"),
    ("Cable solar 6 mm negro", "metro"),
    ("Conector MC4", "par"),
    ("Interruptor termomagnético DC", "pieza"),
    ("Interruptor termomagnético AC", "pieza"),
    ("Cable de puesta a tierra", "metro"),
]


def seed_inventory() -> None:
    """Create the 15-item stock list with zero quantities and unconfigured costs."""
    with SessionLocal() as session:
        if (session.scalar(select(func.count()).select_from(InventoryItem)) or 0) > 0:
            return
        session.add_all([InventoryItem(name=name, unit=unit, quantity=0, minimum_quantity=0, unit_cost=0) for name, unit in DEMO_STOCK_CATALOG])
        session.commit()
