import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, select

from app.models import HistoryCard, Installation, Purchase, Quote, Sale
from app.product_api import _sale_result, _serialize_purchase_invoice, _serialize_quote


def test_quote_and_purchase_serializers_omit_drive_ids_but_preserve_availability() -> None:
    quote = Quote(folio="AE-1", customer_id="customer-1", drive_file_id="private-quote-drive-id")
    purchase = Purchase(folio="AE-C-1", supplier_id="supplier-1", invoice_drive_file_id="private-invoice-drive-id")

    quote_result = _serialize_quote(quote)
    purchase_result = _serialize_purchase_invoice(purchase)

    assert "drive_file_id" not in quote_result
    assert quote_result["drive_available"] is True
    assert "invoice_drive_file_id" not in purchase_result
    assert purchase_result["invoice_available"] is True
    assert "private-quote-drive-id" not in repr(quote_result)
    assert "private-invoice-drive-id" not in repr(purchase_result)


def test_sales_response_uses_private_drive_safe_installation_projection() -> None:
    sale = Sale(
        folio="AE-V-1", customer_id="customer-1", quote_id="quote-1",
        installation_id="installation-1", sale_type="cash", total=100,
    )
    installation = Installation(
        folio="AE-OT-1", customer_id="customer-1", status="assigned",
        material_request_drive_file_id="private-material-request-id",
    )
    db = Mock()
    db.get.side_effect = lambda model, _id: installation if model is Installation else None
    db.scalar.return_value = None
    db.scalars.return_value.all.return_value = []

    result = _sale_result(db, sale)

    assert result["installation"]["material_request_available"] is True
    assert "material_request_drive_file_id" not in result["installation"]
    assert "private-material-request-id" not in repr(result)


def test_private_drive_id_revision_appends_to_us14_and_preserves_literal() -> None:
    root = Path(__file__).parents[1]
    path = root / "alembic" / "versions" / "202611100088_nested_sales_drive_id_privacy_revision.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    HistoryCard.__table__.create(engine)
    records = json.loads((root / "app" / "history_card_initial.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    source = next(row for row in records if row["story_id"] == "US-14")
    literal = source["source_literal"]
    with engine.begin() as connection:
        connection.execute(HistoryCard.__table__.insert(), [{
            **row, "id": str(uuid4()), "recorded_by": "source-import", "created_at": now,
        } for row in records])
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        versions = connection.execute(
            select(HistoryCard.__table__).where(HistoryCard.story_id == "US-14")
            .order_by(HistoryCard.version)
        ).mappings().all()

    assert len(versions) == 2
    assert [row["version"] for row in versions] == [1, 2]
    assert all(row["source_literal"] == literal for row in versions)
    assert len(versions) == 2
    assert versions[1]["iteration"] == "Iteración 76 · privacidad de archivos en ventas · 2026-11-10"
    assert any("ventas" in item for item in versions[1]["acceptance_criteria"])
