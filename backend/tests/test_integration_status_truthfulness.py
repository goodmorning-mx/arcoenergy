from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import product_api
from app.models import Base


def test_folder_id_does_not_claim_drive_is_connected(monkeypatch):
    monkeypatch.setattr(product_api, "settings", SimpleNamespace(
        google_drive_folder_id="folder-123", google_drive_service_account_json="",
        whatsapp_phone="+521234567890", business_snapshot_interval_hours=24,
    ))

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        result = product_api.integration_status(db)

    assert result["google_drive"] == {
        "connected": False,
        "status": "credentials_not_configured",
        "folder_configured": True,
        "service_account_configured": False,
        "stored_file_types": ["quotes", "service_order_requests", "purchase_invoices", "expense_receipts", "business_data_snapshot"],
        "planned_file_types": ["contracts", "identity_documents"],
        "business_snapshot_available": False,
        "business_snapshot_limit_mb": 64,
        "business_snapshot_schedule": {
            "enabled": False, "interval_hours": 24,
            "status": "waiting_for_drive_configuration", "last_attempt_at": None,
            "last_success_at": None, "next_due_at": None, "last_filename": None,
            "last_error_code": None,
        },
    }
    assert result["whatsapp"] == {
        "connected": False,
        "mode": "click_to_chat",
        "status": "click_to_chat_only",
        "business_phone_configured": True,
    }
