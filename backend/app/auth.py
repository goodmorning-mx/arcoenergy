from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from gm_auth import AuthService, AuthSettings
from gm_auth.models import organizations, users

from app.config import get_settings
from app.database import create_database_engine

settings = get_settings()
auth_engine = create_database_engine()
auth_service = AuthService(auth_engine, AuthSettings(settings.auth_secret, issuer="arcoenergy"))


def bootstrap_admin() -> None:
    """Create a runtime-configured admin once; no default credential is shipped."""
    if not settings.admin_bootstrap_email or not settings.admin_bootstrap_password:
        return
    with auth_engine.connect() as connection:
        organization = connection.execute(select(organizations.c.id).where(organizations.c.id == settings.organization_id)).first()
    if organization is None:
        try:
            auth_service.create_organization(organization_id=settings.organization_id, slug="arcoenergy", name="ArcoEnergy")
        except IntegrityError:
            pass
    with auth_engine.connect() as connection:
        admin = connection.execute(select(users.c.id).where(users.c.email == settings.admin_bootstrap_email.lower())).first()
    if admin is None:
        auth_service.create_user(email=settings.admin_bootstrap_email, name="ArcoEnergy Admin", password=settings.admin_bootstrap_password, organization_id=settings.organization_id, roles={"admin"}, permissions={"customers:read", "customers:write", "quotes:read", "quotes:write", "installations:read", "installations:write", "inventory:read", "inventory:write", "inventory:manage", "expenses:read", "expenses:write", "receivables:read", "receivables:write", "team:manage"})
