from types import SimpleNamespace

from app import product_api


def test_folder_id_does_not_claim_drive_is_connected(monkeypatch):
    monkeypatch.setattr(product_api, "settings", SimpleNamespace(google_drive_folder_id="folder-123", whatsapp_phone="+521234567890"))

    result = product_api.integration_status()

    assert result["google_drive"] == {
        "connected": False,
        "status": "credentials_not_configured",
        "folder_configured": True,
        "service_account_configured": False,
        "stored_file_types": ["quotes"],
        "planned_file_types": ["contracts", "receipts"],
    }
    assert result["whatsapp"] == {
        "connected": False,
        "mode": "click_to_chat",
        "status": "click_to_chat_only",
        "business_phone_configured": True,
    }
