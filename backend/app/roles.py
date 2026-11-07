"""ArcoEnergy account roles and their API permissions."""

from types import MappingProxyType

ROLE_LABELS = MappingProxyType({
    "administrador": "Administrador",
    "contador": "Contador",
    "marketing": "Marketing",
    "instalador": "Instalador",
    "cliente": "Cliente",
})

ROLE_PERMISSIONS = MappingProxyType({
    "administrador": frozenset({
        "customers:read", "customers:write", "quotes:read", "quotes:write",
        "installations:read", "installations:write", "inventory:read",
        "inventory:write", "inventory:manage", "inventory:issue", "inventory:costs:read", "expenses:read", "expenses:write",
        "receivables:read", "receivables:write", "accounts:read", "accounts:write", "accounts:manage",
        "suppliers:read", "suppliers:manage", "purchases:read", "purchases:write", "team:manage",
        "sales:read", "sales:write", "reports:read",
    }),
    "contador": frozenset({
        "customers:read", "quotes:read", "installations:read",
        "inventory:read", "inventory:issue", "inventory:costs:read", "expenses:read", "expenses:write", "receivables:read", "receivables:write",
        "accounts:read", "accounts:write", "accounts:manage", "suppliers:read", "suppliers:manage", "purchases:read", "purchases:write",
        "sales:read", "sales:write", "reports:read",
    }),
    "marketing": frozenset({
        "customers:read", "customers:write", "quotes:read", "quotes:write",
    }),
    "instalador": frozenset({
        "installations:read", "inventory:read", "inventory:write",
        "expenses:write",
    }),
    # Client access is limited to a separate endpoint that filters every row by
    # the account email. It does not grant access to internal CRM collections.
    "cliente": frozenset({"client:portal"}),
})

LEGACY_ROLE_ALIASES = MappingProxyType({
    "admin": "administrador",
    "ventas": "marketing",
    "finanzas": "contador",
})


def canonical_role(role: str) -> str:
    normalized = role.strip().lower()
    return LEGACY_ROLE_ALIASES.get(normalized, normalized)
