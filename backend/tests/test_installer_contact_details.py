from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InstallationAssignment
from app.product_api import list_installations
from app.roles import ROLE_PERMISSIONS


def test_installer_sees_contact_details_only_for_assigned_installations():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    installer = AuthIdentity(
        "installer-1", "arcoenergy", frozenset({"instalador"}),
        ROLE_PERMISSIONS["instalador"], "field@example.test", "Campo",
    )
    with Session(engine) as db:
        customer = Customer(
            name="Cliente solar", city="Tampico", address="Calle Sol 10",
            phone="8331234567", email="cliente@example.test", status="lead",
            source="public_web",
        )
        other_customer = Customer(name="Otra persona", phone="8337654321")
        db.add_all([customer, other_customer]); db.flush()
        assigned = Installation(customer_id=customer.id, folio="AE-OT-1", lead_installer="other@example.test")
        not_assigned = Installation(customer_id=other_customer.id, folio="AE-OT-2", lead_installer="different@example.test")
        db.add_all([assigned, not_assigned]); db.flush()
        db.add(InstallationAssignment(
            installation_id=assigned.id, installer_email="field@example.test", assigned_by="admin@example.test",
        ))
        db.commit()

        result = list_installations(installer, db)

    assert [item["folio"] for item in result] == ["AE-OT-1"]
    assert result[0]["customer"] == {
        "id": customer.id,
        "name": "Cliente solar",
        "city": "Tampico",
        "address": "Calle Sol 10",
        "phone": "8331234567",
        "email": "cliente@example.test",
    }
    assert "status" not in result[0]["customer"]
    assert "source" not in result[0]["customer"]
