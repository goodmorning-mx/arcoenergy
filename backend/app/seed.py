from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import InventoryItem, QuotePackage
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


def seed_quote_catalog() -> None:
    """Seed a visibly provisional catalog so the first demo is navigable.

    These values are copied from the previous mock UI only. They remain marked
    demo until an administrator replaces and explicitly approves them.
    """
    with SessionLocal() as session:
        if (session.scalar(select(func.count()).select_from(QuotePackage)) or 0) > 0:
            return
        packages = []
        for count in range(4, 21):
            kw = count * 610 / 1000
            inverter = "Growatt 3 kW" if kw <= 3.7 else "Growatt 5 kW" if kw <= 5.5 else "Huawei 6 kW" if kw <= 8 else "Huawei 10 kW"
            inverter_price = 16800 if kw <= 3.7 else 22900 if kw <= 5.5 else 31900 if kw <= 8 else 44800
            packages.append(QuotePackage(
                panel_count=count,
                panel_brand="Jinko",
                panel_watts=610,
                panel_unit_price=13250,
                structure_name="Estructura de aluminio",
                structure_price=14900,
                inverter_options=[{"name": inverter, "price_mxn": inverter_price}],
                default_inverter=inverter,
                payment_methods=["Contado", "Financiamiento", "Plan 24"],
                enabled=True,
                is_demo=True,
            ))
        session.add_all(packages)
        session.commit()
