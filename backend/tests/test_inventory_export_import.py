from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import Base, HistoryCard, HistoryCardReview, InventoryImportBatch, InventoryItem, InventoryMovement, Project, Supplier
from scripts import import_inventory_export


def make_export(path: Path) -> None:
    files = {
        "dashboard_2026-11-24.csv": (["Indicador", "Valor", "Fecha de corte"], [["Total de productos", "1", "2026-11-24"]]),
        "dashboard_detalle_2026-11-24.csv": (["Sección", "Producto", "Folio", "Tipo", "Cantidad", "Stock actual", "Stock mínimo", "Fecha"], [["Stock bajo", "Panel solar", "", "", "", "12", "2", "2026-11-24"]]),
        "inventario_2026-11-24.csv": (["Categoría", "Código", "Producto", "Subcategoría", "Stock", "Nivel", "Costo", "Ubicación", "Estatus"], [["Paneles", "A-1", "Panel solar", "FV", "12", "OK", "5000", "Almacén", "Activo"], ["Inversores", "A-2", "Inversor", "Potencia", "4", "OK", "12000", "Almacén", "Activo"]]),
        "entradas_2026-11-24.csv": (["Folio", "Producto", "Cantidad", "Proveedor", "Factura", "Responsable", "Fecha"], [["ENT-1", "Panel solar", "12", "Proveedor Solar", "FAC-1", "almacenista@example.test", "24 nov 2026 10:00"], ["ENT-1", "Inversor", "4", "Proveedor Solar", "FAC-1", "almacenista@example.test", "24 nov 2026 10:00"]]),
        "salidas_2026-11-24.csv": (["Folio", "Producto", "Cantidad", "Proyecto", "Departamento", "Responsable", "Fecha", "Cantidad devuelta"], [["SAL-1", "Panel solar", "2", "Instalación Norte", "Técnicos", "campo@example.test", "24 nov 2026 11:00", "0"]]),
        "kardex_2026-11-24.csv": (["Producto", "Código", "Fecha", "Tipo", "Folio", "Entrada", "Salida", "Saldo", "Usuario"], [["Panel solar", "A-1", "24 nov 2026 10:00", "Entrada", "ENT-1", "12", "0", "12", "almacenista"], ["Inversor", "A-2", "24 nov 2026 10:00", "Entrada", "ENT-1", "4", "0", "4", "almacenista"], ["Panel solar", "A-1", "24 nov 2026 11:00", "Salida", "SAL-1", "0", "2", "10", "campo"]]),
        "proveedores_2026-11-24.csv": (["Nombre", "Contacto", "Email", "Teléfono", "RFC"], [["Proveedor Solar", "Ana", "proveedor@example.test", "5550101010", "RFC123"]]),
        "proyectos_2026-11-24.csv": (["Nombre", "Código", "Cliente", "Ubicación", "Estatus", "Prioridad", "Avance (%)", "Responsable", "Fecha límite", "Monto del contrato"], [["Instalación Norte", "AE-2026-1", "Cliente Demo", "Tampico", "En proceso", "Alta", "50", "Josue", "30/11/2026", "100000"]]),
    }
    with zipfile.ZipFile(path, "w") as archive:
        for filename, (headers, rows) in files.items():
            text = io.StringIO()
            writer = csv.writer(text)
            writer.writerow(headers)
            writer.writerows(rows)
            archive.writestr(filename, "\ufeff" + text.getvalue())


def test_inventory_export_import_is_idempotent_and_does_not_reapply_historical_stock(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'inventory-test.db'}")
    Base.metadata.create_all(engine)
    archive = tmp_path / "arco-export.zip"
    make_export(archive)
    monkeypatch.setattr(import_inventory_export, "create_database_engine", lambda: engine)

    first = import_inventory_export.import_archive(archive)
    second = import_inventory_export.import_archive(archive)

    assert first["status"] == "imported"
    assert first["products"] == 2 and first["imported_movements"] == 3
    assert second["status"] == "already_imported"
    with Session(engine) as db:
        item = db.scalar(select(InventoryItem).where(InventoryItem.code == "A-1"))
        assert item is not None and item.quantity == 12 and item.minimum_quantity == 2
        assert db.scalar(select(InventoryMovement).where(InventoryMovement.movement_type == "in")).folio == "ENT-1"
        assert db.scalar(select(InventoryMovement).where(InventoryMovement.movement_type == "out")).project_id is not None
        assert db.scalar(select(Project).where(Project.code == "AE-2026-1")).progress_percent == 50
        assert db.scalar(select(Supplier).where(Supplier.name == "Proveedor Solar")) is not None
        assert db.query(InventoryImportBatch).count() == 1
        assert db.query(InventoryMovement).count() == 3


def test_inventory_export_migration_removes_unique_folio_and_adds_project_link():
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from importlib.util import module_from_spec, spec_from_file_location
    from sqlalchemy import inspect, text

    migration_path = Path(__file__).parents[1] / "alembic" / "versions" / "202611240161_inventory_import_and_project_financial_fields.py"
    spec = spec_from_file_location("inventory_export_migration", migration_path)
    migration = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ae_projects (id VARCHAR(36) PRIMARY KEY, code VARCHAR(40) NOT NULL, customer_id VARCHAR(36) NOT NULL, name VARCHAR(180) NOT NULL, notes TEXT NOT NULL, created_by VARCHAR(180) NOT NULL, created_at DATETIME NOT NULL)"))
        connection.execute(text("CREATE TABLE ae_inventory_movements (id VARCHAR(36) PRIMARY KEY, folio VARCHAR(40) NOT NULL)"))
        connection.execute(text("CREATE UNIQUE INDEX ix_ae_inventory_movements_folio ON ae_inventory_movements (folio)"))
        HistoryCard.__table__.create(connection)
        HistoryCardReview.__table__.create(connection)
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        connection.execute(text("INSERT INTO ae_inventory_movements (id, folio) VALUES ('m1','DOC-1'), ('m2','DOC-1')"))
        indexes = inspect(connection).get_indexes("ae_inventory_movements")
        assert any(index["name"] == "ix_ae_inventory_movements_folio" and not index["unique"] for index in indexes)
        assert "project_id" in {column["name"] for column in inspect(connection).get_columns("ae_inventory_movements")}
        assert connection.execute(text("SELECT COUNT(*) FROM ae_history_cards WHERE story_id='US-46'")).scalar_one() == 1
        assert connection.execute(text("SELECT COUNT(*) FROM ae_history_card_reviews WHERE story_id='US-46'")).scalar_one() == 1

