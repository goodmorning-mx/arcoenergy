from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from gm_auth.models import AuthIdentity

from app.models import Base, Customer, Installation, InstallationAssignment, InventoryItem, WorkOrderMaterial
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


def test_installation_materials_report_shortage_against_other_orders_reservations():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    manager = AuthIdentity(
        "manager-1", "arcoenergy", frozenset({"administrador"}),
        ROLE_PERMISSIONS["administrador"], "admin@example.test", "Administración",
    )
    with Session(engine) as db:
        customer_a = Customer(name="Proyecto A", city="Tampico")
        customer_b = Customer(name="Proyecto B", city="Madero")
        item = InventoryItem(name="Panel solar", quantity=10, unit="pieza")
        db.add_all([customer_a, customer_b, item]); db.flush()
        order_a = Installation(customer_id=customer_a.id, folio="AE-OT-A", lead_installer="a@example.test")
        order_b = Installation(customer_id=customer_b.id, folio="AE-OT-B", lead_installer="b@example.test")
        db.add_all([order_a, order_b]); db.flush()
        db.add_all([
            WorkOrderMaterial(installation_id=order_a.id, item_id=item.id, requested_quantity=8),
            WorkOrderMaterial(installation_id=order_b.id, item_id=item.id, requested_quantity=8),
        ])
        db.commit()

        result = list_installations(manager, db)
        installer_a = AuthIdentity(
            "installer-a", "arcoenergy", frozenset({"instalador"}),
            ROLE_PERMISSIONS["instalador"], "a@example.test", "Instalador A",
        )
        field_result = list_installations(installer_a, db)

    by_folio = {order["folio"]: order for order in result}
    for folio in ("AE-OT-A", "AE-OT-B"):
        line = by_folio[folio]["materials"][0]
        assert line["available_for_order"] == 2
        assert line["shortage_quantity"] == 6
    assert [order["folio"] for order in field_result] == ["AE-OT-A"]
    field_material = field_result[0]["materials"][0]
    assert field_material["item_name"] == "Panel solar"
    assert field_material["requested_quantity"] == 8
    assert field_material["available_for_order"] == 2
    assert field_material["shortage_quantity"] == 6
