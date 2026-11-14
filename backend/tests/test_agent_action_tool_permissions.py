from gm_auth.models import AuthIdentity

from app.product_api import _agent_registry
from app.roles import ROLE_PERMISSIONS


def _identity(role):
    return AuthIdentity(
        f"{role}-user", "arcoenergy", frozenset({role}), ROLE_PERMISSIONS[role],
        f"{role}@example.test", role.title(),
    )


def test_agent_write_tool_is_available_only_to_current_customer_writers():
    admin_tools = {row["name"]: row for row in _agent_registry("internal", _identity("administrador")).list()}
    marketing_tools = {row["name"]: row for row in _agent_registry("internal", _identity("marketing")).list()}
    accounting_tools = {row["name"]: row for row in _agent_registry("internal", _identity("contador")).list()}
    public_tools = {row["name"]: row for row in _agent_registry("public").list()}

    write_tool = "arcoenergy.schedule_followup"
    assert write_tool in admin_tools and write_tool in marketing_tools
    assert write_tool not in accounting_tools and write_tool not in public_tools
    assert admin_tools[write_tool]["metadata"]["readOnly"] is False
    assert admin_tools[write_tool]["metadata"]["requiresConfirmation"] is True
    assert set(public_tools) == {"arcoenergy.public_system_sizes"}
