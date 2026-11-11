import re

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.main import app
from app.product_api import router


PUBLIC_PRODUCT_ROUTES = {
    ("POST", "/v1/public/leads"),
    ("POST", "/v1/public/agent/chat"),
}


def test_only_explicitly_public_product_routes_may_skip_bearer_auth() -> None:
    routes = [route for route in router.routes if isinstance(route, APIRoute)]
    public_routes = {
        (method, route.path)
        for route in routes
        for method in route.methods or ()
        if (method, route.path) in PUBLIC_PRODUCT_ROUTES
    }
    assert public_routes == PUBLIC_PRODUCT_ROUTES

    unprotected = []
    for route in routes:
        for method in route.methods or ():
            if method in {"HEAD", "OPTIONS"} or (method, route.path) in PUBLIC_PRODUCT_ROUTES:
                continue
            requirements = []

            def collect_security(dependant) -> None:
                requirements.extend(dependant.security_requirements)
                for dependency in dependant.dependencies:
                    collect_security(dependency)

            collect_security(route.dependant)
            if not requirements:
                unprotected.append(f"{method} {route.path}")

    assert unprotected == []


def test_every_private_product_get_route_rejects_anonymous_requests() -> None:
    client = TestClient(app)
    private_get_routes = [
        route
        for route in router.routes
        if isinstance(route, APIRoute)
        and "GET" in (route.methods or ())
        and ("GET", route.path) not in PUBLIC_PRODUCT_ROUTES
    ]
    assert private_get_routes

    for route in private_get_routes:
        path = re.sub(r"\{[^}]+\}", "00000000-0000-4000-8000-000000000000", route.path)
        response = client.get(path, params={"phone": "+521234567890", "message": "auth-audit"})
        assert response.status_code in {401, 403}, f"{route.path} returned {response.status_code} without authentication"
