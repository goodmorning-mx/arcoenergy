from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import product_api
from app.models import Base, Customer
from app.roles import ROLE_PERMISSIONS
from gm_auth.models import AuthIdentity


def _identity(email: str) -> AuthIdentity:
    return AuthIdentity(
        "customer-user", "arcoenergy", frozenset({"cliente"}),
        ROLE_PERMISSIONS["cliente"], email, "Rosa Martínez",
    )


def test_administrator_can_create_client_login_only_for_existing_customer_email(monkeypatch) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(Customer(name="Rosa Martínez", email="rosa@example.com", city="Tampico"))
        db.commit()

    created_identity = _identity("rosa@example.com")
    create_user = Mock(return_value=created_identity)
    monkeypatch.setattr(product_api, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr(product_api.auth_service, "create_user", create_user)

    result = product_api.team_create(product_api.TeamMemberInput(
        name="Rosa Martínez", email=" ROSA@example.com ",
        password="una-clave-segura-de-prueba", role="cliente",
    ))

    assert result["email"] == "rosa@example.com"
    assert result["roles"] == ["cliente"]
    assert result["permissions"] == ["client:portal"]
    create_user.assert_called_once_with(
        email="rosa@example.com", name="Rosa Martínez",
        password="una-clave-segura-de-prueba", organization_id=product_api.settings.organization_id,
        roles={"cliente"}, permissions={"client:portal"},
    )


def test_client_login_is_not_created_without_matching_customer_record(monkeypatch) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    create_user = Mock()
    monkeypatch.setattr(product_api, "SessionLocal", lambda: Session(engine))
    monkeypatch.setattr(product_api.auth_service, "create_user", create_user)

    with pytest.raises(HTTPException) as error:
        product_api.team_create(product_api.TeamMemberInput(
            name="Rosa Martínez", email="rosa@example.com",
            password="una-clave-segura-de-prueba", role="cliente",
        ))

    assert error.value.status_code == 422
    assert "Registra primero al cliente" in error.value.detail
    create_user.assert_not_called()
