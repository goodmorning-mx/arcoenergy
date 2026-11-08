from datetime import date
from decimal import Decimal

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, ProjectExpense
from app.product_api import get_expense_receipt_file, list_expenses, upload_expense_receipt_file
from app.roles import ROLE_PERMISSIONS
from gm_auth.models import AuthIdentity


class UploadRequest:
    def __init__(self, content: bytes, content_type: str = "application/pdf", filename: str = "ticket.pdf"):
        self.headers = {
            "content-type": content_type,
            "content-length": str(len(content)),
            "x-document-name": filename,
        }
        self.content = content

    async def stream(self):
        yield self.content


def accountant() -> AuthIdentity:
    return AuthIdentity("accountant", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "contador@example.test", "Contador")


@pytest.mark.anyio
async def test_expense_receipt_is_saved_privately_and_downloaded_through_authenticated_endpoint(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    stored = {}
    def save_file(**kwargs):
        stored.update(kwargs)
        return "private-drive-file-id"
    monkeypatch.setattr("app.product_api.save_private_file", save_file)
    with Session(engine) as db:
        expense = ProjectExpense(category="Viáticos", description="Gasolina", amount=Decimal("500"), occurred_on=date(2026, 11, 8))
        db.add(expense); db.commit(); db.refresh(expense)
        result = await upload_expense_receipt_file(expense.id, UploadRequest(b"%PDF-1.7\nreceipt"), accountant(), db)
        assert result["saved"] is True
        assert stored["filename"] == f"gasto-{expense.id}-ticket.pdf"
        db.refresh(expense)
        assert expense.receipt_drive_file_id == "private-drive-file-id"
        assert expense.receipt_filename == "ticket.pdf"
        assert expense.receipt_content_type == "application/pdf"
        listed = list_expenses(db)[0]
        assert listed["receipt_drive_available"] is True
        assert listed["receipt_filename"] == "ticket.pdf"
        assert "receipt_drive_file_id" not in listed

        monkeypatch.setattr("app.product_api.download_private_file", lambda file_id: httpx.Response(200, content=b"%PDF-1.7\nreceipt"))
        response = get_expense_receipt_file(expense.id, accountant(), db)

    assert response.media_type == "application/pdf"
    assert response.body == b"%PDF-1.7\nreceipt"
    assert "ticket.pdf" in response.headers["content-disposition"]


@pytest.mark.anyio
async def test_expense_receipt_rejects_unsupported_or_mismatched_content(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        expense = ProjectExpense(category="Viáticos", description="Gasolina", amount=Decimal("500"), occurred_on=date(2026, 11, 8))
        db.add(expense); db.commit()
        with pytest.raises(HTTPException) as unsupported:
            await upload_expense_receipt_file(expense.id, UploadRequest(b"x", "text/plain", "x.txt"), accountant(), db)
        with pytest.raises(HTTPException) as mismatched:
            await upload_expense_receipt_file(expense.id, UploadRequest(b"not a pdf"), accountant(), db)

    assert unsupported.value.status_code == 415
    assert mismatched.value.status_code == 415


@pytest.mark.anyio
async def test_expense_receipt_reports_drive_not_configured_without_leaking_provider_errors(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.product_api.save_private_file", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("not_configured")))
    with Session(engine) as db:
        expense = ProjectExpense(category="Viáticos", description="Gasolina", amount=Decimal("500"), occurred_on=date(2026, 11, 8))
        db.add(expense); db.commit()
        with pytest.raises(HTTPException) as unavailable:
            await upload_expense_receipt_file(expense.id, UploadRequest(b"%PDF-1.7\nreceipt"), accountant(), db)

    assert unavailable.value.status_code == 503
    assert unavailable.value.detail == "drive_not_configured"


@pytest.mark.anyio
async def test_installer_cannot_attach_receipt_to_unassigned_or_general_expense():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity("installer", "arcoenergy", frozenset({"instalador"}), ROLE_PERMISSIONS["instalador"], "field@example.test", "Instalador")
    with Session(engine) as db:
        expense = ProjectExpense(category="Viáticos", description="Gasolina", amount=Decimal("500"), occurred_on=date(2026, 11, 8))
        db.add(expense); db.commit()
        with pytest.raises(HTTPException) as forbidden:
            await upload_expense_receipt_file(expense.id, UploadRequest(b"%PDF-1.7\\nreceipt"), installer, db)

    assert forbidden.value.status_code == 403
