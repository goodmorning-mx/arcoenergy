import ast
from pathlib import Path


PUBLIC_API_ROUTES = {
    ("post", "/public/leads"),
    ("post", "/public/agent/chat"),
}
AUTHORIZATION_DEPENDENCIES = {"require_permissions", "require_any_permission"}


def test_every_non_public_product_api_route_declares_authorization() -> None:
    source_path = Path(__file__).parents[1] / "app" / "product_api.py"
    module = ast.parse(source_path.read_text())
    missing: list[str] = []

    for node in module.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if not isinstance(decorator.func.value, ast.Name) or decorator.func.value.id != "router":
                continue
            method = decorator.func.attr.lower()
            path = ast.literal_eval(decorator.args[0]) if decorator.args else ""
            route = (method, path)
            if route in PUBLIC_API_ROUTES:
                continue
            authorization = ast.unparse(decorator)
            signature = ast.unparse(node.args)
            if not any(name in authorization or name in signature for name in AUTHORIZATION_DEPENDENCIES):
                missing.append(f"{method.upper()} /v1{path} ({node.name})")

    assert not missing, "Product API routes missing an explicit permission dependency:\n" + "\n".join(missing)
