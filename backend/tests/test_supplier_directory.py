from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Base, Purchase, Supplier
from app.product_api import SupplierInput, create_supplier, list_suppliers
from app.roles import ROLE_PERMISSIONS
from gm_auth.models import AuthIdentity


def test_supplier_directory_normalizes_terms_and_lists_open_payable_balance() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    identity = AuthIdentity("accountant-1", "arcoenergy", frozenset({"contador"}), ROLE_PERMISSIONS["contador"], "conta@example.test", "Contador")
    with Session(engine) as db:
        supplier = create_supplier(SupplierInput(
            name="  Proveedor Solar  ", rfc="aaa010101aaa", email=" VENTAS@SOLAR.MX ",
            payment_terms="credit", credit_days=15,
        ), identity, db)
        stored = db.get(Supplier, supplier["id"])
        db.add(Purchase(supplier_id=stored.id, folio="AE-C-TEST", payment_terms="credit", purchase_date=date.today(),
                        total=Decimal("1200"), paid_amount=Decimal("200"), status="partially_paid"))
        db.commit()
        rows = list_suppliers(db)
        assert rows[0]["name"] == "Proveedor Solar"
        assert rows[0]["rfc"] == "AAA010101AAA"
        assert rows[0]["email"] == "ventas@solar.mx"
        assert rows[0]["payment_terms"] == "credit" and rows[0]["credit_days"] == 15
        assert rows[0]["current_balance"] == Decimal("1000.00")
        with pytest.raises(ValidationError):
            create_supplier(SupplierInput(name="Proveedor sin plazo", payment_terms="credit", credit_days=0), identity, db)
