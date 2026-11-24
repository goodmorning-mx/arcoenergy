"""Idempotently import the latest Arco Energy inventory export ZIP.

The source archive is deliberately supplied at runtime and is never committed.
Historical movements are inserted without changing the catalog snapshot stock.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import create_database_engine
from app.models import (
    Customer, InventoryCategory, InventoryImportBatch, InventoryItem,
    InventoryMovement, Project, Supplier,
)


MONTHS = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
          "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}


def norm(value: str) -> str:
    folded = unicodedata.normalize("NFKD", (value or "").casefold())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", folded).split())


def number(value: str | None, default: Decimal | None = Decimal("0")) -> Decimal | None:
    raw = (value or "").strip().replace("$", "").replace(",", "").replace("MXN", "").strip()
    if not raw or raw in {"—", "-"}:
        return default
    return Decimal(raw)


def parse_date(value: str, *, date_only: bool = False):
    raw = (value or "").strip()
    if not raw or raw in {"—", "-"}:
        return None
    try:
        parsed_iso = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed_iso.tzinfo is None:
            parsed_iso = parsed_iso.replace(tzinfo=ZoneInfo("America/Cancun"))
        return parsed_iso.date() if date_only else parsed_iso
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.date() if date_only else parsed.replace(tzinfo=ZoneInfo("America/Cancun"))
        except ValueError:
            pass
    match = re.fullmatch(r"(\d{1,2})\s+([a-zA-ZñÑ]{3})\s+(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", raw, re.I)
    if match:
        day, month_name, year, hour, minute = match.groups()
        month = MONTHS.get(month_name.casefold()[:3])
        if not month:
            raise ValueError(f"Fecha no reconocida en CSV: {raw}")
        parsed = datetime(int(year), month, int(day), int(hour or 12), int(minute or 0), tzinfo=ZoneInfo("America/Cancun"))
        return parsed.date() if date_only else parsed
    raise ValueError(f"Fecha no reconocida en CSV: {raw}")


def read_csv(archive: zipfile.ZipFile, prefix: str) -> list[dict[str, str]]:
    matches = [name for name in archive.namelist() if Path(name).name.startswith(prefix) and name.lower().endswith(".csv") and not (prefix == "dashboard_" and "detalle" in Path(name).name)]
    if len(matches) != 1:
        raise ValueError(f"Se esperaba un CSV para {prefix}; encontrados: {len(matches)}")
    with archive.open(matches[0]) as source:
        rows = list(csv.DictReader(io.TextIOWrapper(source, encoding="utf-8-sig", newline="")))
    return [{(key or "").strip(): (value or "").strip() for key, value in row.items()} for row in rows]


def external_key(*parts: object) -> str:
    payload = json.dumps(parts, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def import_archive(path: Path, imported_by: str = "inventory-export-import") -> dict:
    archive_bytes = path.read_bytes()
    digest = hashlib.sha256(archive_bytes).hexdigest()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        catalog = read_csv(archive, "inventario_")
        entries = read_csv(archive, "entradas_")
        exits = read_csv(archive, "salidas_")
        ledger = read_csv(archive, "kardex_")
        low_stock = [row for row in read_csv(archive, "dashboard_detalle_") if norm(row.get("Sección", "")) == "stock bajo"]
        suppliers = read_csv(archive, "proveedores_")
        projects = read_csv(archive, "proyectos_")
        dashboard = read_csv(archive, "dashboard_")

    if len(entries) + len(exits) != len(ledger):
        raise ValueError(f"El Kardex ({len(ledger)}) no coincide con entradas + salidas ({len(entries) + len(exits)}); no se importó nada.")
    if len({row["Código"].upper() for row in catalog}) != len(catalog):
        raise ValueError("Hay códigos de producto repetidos; no se importó nada.")
    product_names = {norm(row["Producto"]) for row in catalog}
    movement_names = {norm(row.get("Producto", "")) for row in entries + exits}
    expected_ledger: Counter = Counter()
    for row in entries:
        expected_ledger[(row["Folio"], norm(row["Producto"]), "entrada", number(row["Cantidad"]))] += 1
    for row in exits:
        expected_ledger[(row["Folio"], norm(row["Producto"]), "salida", number(row["Cantidad"]))] += 1
    export_ledger: Counter = Counter()
    for row in ledger:
        direction = "entrada" if number(row.get("Entrada")) > 0 else "salida"
        quantity = row.get("Entrada") if direction == "entrada" else row.get("Salida")
        export_ledger[(row["Folio"], norm(row["Producto"]), direction, number(quantity))] += 1
    if expected_ledger != export_ledger:
        raise ValueError("Los renglones de entradas/salidas no coinciden con el Kardex; no se importó nada.")

    minimum_by_name = {norm(row["Producto"]): number(row.get("Stock mínimo")) for row in low_stock}
    legacy_names = movement_names - product_names
    aliases = {norm("interruptor termomagnetico 2 polos 40a ac"): norm("interruptor termomagnetico din 2 polos 40a ac")}
    aliased_names = {source for source, target in aliases.items() if target in product_names}
    history_only_names = legacy_names - aliased_names
    summary = {"products": len(catalog), "legacy_history_only_products": len(history_only_names), "entries": len(entries), "exits": len(exits), "kardex": len(ledger),
               "suppliers": len(suppliers), "projects": len(projects), "dashboard_rows": len(dashboard)}
    engine = create_database_engine()
    try:
        with Session(engine, expire_on_commit=False) as db:
            existing_batch = db.scalar(select(InventoryImportBatch).where(InventoryImportBatch.source_sha256 == digest))
            if existing_batch:
                return {"status": "already_imported", **(existing_batch.summary or {})}

            categories: dict[str, InventoryCategory] = {}
            for row in catalog:
                category_name = row["Categoría"].strip()[:100]
                category_key = " ".join(category_name.casefold().split())[:120]
                if category_key not in categories:
                    category = db.scalar(select(InventoryCategory).where(InventoryCategory.name_key == category_key))
                    if category is None:
                        category = InventoryCategory(name=category_name, name_key=category_key, created_by=imported_by)
                        db.add(category); db.flush()
                    categories[category_key] = category

            supplier_by_name: dict[str, Supplier] = {}
            for row in suppliers:
                name = row["Nombre"].strip()
                if not name:
                    continue
                key = norm(name)
                supplier = db.scalar(select(Supplier).where(Supplier.name.ilike(name)))
                if supplier is None:
                    supplier = next((candidate for candidate in db.scalars(select(Supplier)).all() if norm(candidate.name) == key), None)
                if supplier is None:
                    supplier = Supplier(name=name, created_by=imported_by)
                    db.add(supplier)
                supplier.contact_name = row.get("Contacto", "")
                supplier.email = row.get("Email", "")
                supplier.phone = row.get("Teléfono", "")
                supplier.rfc = row.get("RFC", "")
                supplier.active = True
                supplier_by_name[key] = supplier
            db.flush()

            item_by_code: dict[str, InventoryItem] = {}
            for row in catalog:
                code = row["Código"].strip().upper()
                category_name = row["Categoría"].strip()[:100]
                category = categories[" ".join(category_name.casefold().split())[:120]]
                quantity = number(row.get("Stock"))
                explicit_min = minimum_by_name.get(norm(row.get("Producto", "")))
                minimum = explicit_min if explicit_min is not None else (Decimal("1") if quantity == 0 else Decimal("0"))
                item = db.scalar(select(InventoryItem).where(InventoryItem.code == code))
                if item is None:
                    item = InventoryItem(code=code, name=row["Producto"][:180])
                    db.add(item)
                item.name = row["Producto"][:180]
                item.category = category_name
                item.category_id = category.id
                item.subcategory = row.get("Subcategoría", "")[:100]
                item.location = row.get("Ubicación", "")[:120]
                item.active = norm(row.get("Estatus", "activo")) != "inactivo"
                item.unit = "pieza"
                item.quantity = quantity
                item.minimum_quantity = minimum
                item.unit_cost = number(row.get("Costo"))
                item_by_code[code] = item
            db.flush()

            customer_by_name: dict[str, Customer] = {}
            existing_customers = db.scalars(select(Customer)).all()
            for customer in existing_customers:
                customer_by_name.setdefault(norm(customer.name), customer)
            project_by_code: dict[str, Project] = {}
            for row in projects:
                code = row["Código"].strip()[:40]
                customer_name = row.get("Cliente", "").strip() or f"Cliente por identificar · {code}"
                customer_key = norm(customer_name)
                customer = customer_by_name.get(customer_key)
                if customer is None:
                    customer = Customer(name=customer_name[:180], city=row.get("Ubicación", "")[:120], status="customer", source="inventory_export")
                    db.add(customer); db.flush()
                    customer_by_name[customer_key] = customer
                project = db.scalar(select(Project).where(Project.code == code))
                raw_status = row.get("Estatus", "")
                normalized_status = norm(raw_status)
                status = "completed" if any(word in normalized_status for word in ("completado", "terminado", "finalizado")) else "active" if any(word in normalized_status for word in ("activo", "proceso", "instalacion")) else "planning"
                if project is None:
                    project = Project(code=code, customer_id=customer.id, name=row["Nombre"][:180], created_by=imported_by)
                    db.add(project)
                project.customer_id = customer.id
                project.name = row["Nombre"][:180]
                project.location = row.get("Ubicación", "")[:240]
                project.status = status
                project.source_status = raw_status[:80]
                project.priority = norm(row.get("Prioridad", "media"))[:30] or "medium"
                project.progress_percent = number(row.get("Avance (%)"))
                project.due_date = parse_date(row.get("Fecha límite", ""), date_only=True)
                project.contract_amount = number(row.get("Monto del contrato"), default=None)
                project.source = "inventory_export"
                project_by_code[code] = project
            db.flush()

            movement_count = 0
            product_by_name = {norm(item.name): item for item in item_by_code.values()}
            historical_category = None
            if legacy_names:
                category_key = "legacy-history-only"
                historical_category = db.scalar(select(InventoryCategory).where(InventoryCategory.name_key == category_key))
                if historical_category is None:
                    historical_category = InventoryCategory(name="Histórico (fuera de catálogo)", name_key=category_key, description="Artículos conservados solo para enlazar movimientos históricos; no son existencias actuales.", active=False, created_by=imported_by)
                    db.add(historical_category); db.flush()
            # This exact alias only normalizes a reordered DIN descriptor; electrical rating stays identical.
            for legacy_name in sorted(legacy_names):
                if legacy_name in aliases and aliases[legacy_name] in product_by_name:
                    continue
                raw_name = next(row["Producto"] for row in entries + exits if norm(row.get("Producto", "")) == legacy_name)
                code = f"LEG-{hashlib.sha256(legacy_name.encode('utf-8')).hexdigest()[:12].upper()}"
                item = db.scalar(select(InventoryItem).where(InventoryItem.code == code))
                if item is None:
                    item = InventoryItem(code=code, name=raw_name[:180])
                    db.add(item)
                item.category = "Histórico (fuera de catálogo)"
                item.category_id = historical_category.id
                item.subcategory = "Solo movimientos históricos"
                item.description = "Artículo fuera del catálogo al corte de la exportación; registro inactivo para conservar el Kardex histórico."
                item.active = False
                item.unit = "pieza"
                item.quantity = Decimal("0")
                item.minimum_quantity = Decimal("0")
                item.unit_cost = Decimal("0")
                product_by_name[legacy_name] = item
            db.flush()

            for movement_type, rows in (("in", entries), ("out", exits)):
                for row in rows:
                    product_name = row.get("Producto", "")
                    code = row.get("Código", "").strip().upper()
                    item = item_by_code.get(code) if code else None
                    product_name_key = norm(product_name)
                    if item is None:
                        item = product_by_name.get(aliases.get(product_name_key, product_name_key))
                    if item is None:
                        raise ValueError(f"No se pudo relacionar un movimiento del Kardex al catálogo ({movement_type}, producto normalizado: {product_name_key}); no se importó nada.")
                    folio = row.get("Folio", "").strip()[:80]
                    when = parse_date(row.get("Fecha", ""))
                    quantity = abs(number(row.get("Cantidad")))
                    if movement_type == "in":
                        supplier_name = row.get("Proveedor", "").strip()
                        supplier = supplier_by_name.get(norm(supplier_name))
                        project = None
                        department = ""
                        invoice = row.get("Factura", "")[:100]
                        origin_ref = f"{folio} · {invoice}".strip(" ·")
                    else:
                        supplier = None
                        project_name = row.get("Proyecto", "").strip()
                        project = next((p for p in project_by_code.values() if norm(p.name) == norm(project_name)), None)
                        department = row.get("Departamento", "")[:100]
                        invoice = ""
                        origin_ref = f"{folio} · {project_name}".strip(" ·")
                    key = external_key("arcoenergy-legacy", movement_type, folio, item.code, when.isoformat(), quantity, invoice, origin_ref)
                    if db.scalar(select(InventoryMovement.id).where(InventoryMovement.source_key == key)):
                        continue
                    db.add(InventoryMovement(
                        id=str(uuid4()), folio=folio or None, source_key=key, item_id=item.id,
                        project_id=project.id if project else None, quantity=quantity,
                        movement_type=movement_type, unit_cost=None, supplier_id=supplier.id if supplier else None,
                        invoice_reference=invoice, source_type="legacy_import", source_reference=origin_ref[:180],
                        department=department, reason="Importación del historial de inventario", created_by=row.get("Responsable", "")[:180],
                        created_at=when,
                    ))
                    movement_count += 1

            db.add(InventoryImportBatch(
                id=str(uuid4()), source_sha256=digest, source_filename=path.name,
                summary={**summary, "imported_movements": movement_count}, imported_by=imported_by,
            ))
            db.commit()
            return {"status": "imported", **summary, "imported_movements": movement_count}
    except Exception:
        raise
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ZIP export containing inventory CSV files")
    parser.add_argument("--imported-by", default="inventory-export-import")
    args = parser.parse_args()
    print(json.dumps(import_archive(args.archive, args.imported_by), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
