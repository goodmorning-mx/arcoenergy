from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_service_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "GoodMorning MVP Template API",
        "status": "ok",
        "environment": "local",
    }


def test_version_endpoint_exposes_coolify_source_commit(monkeypatch) -> None:
    from app import main

    monkeypatch.setattr(main.settings, "source_commit", "a1b2c3d4e5f6")
    response = TestClient(main.app).get("/version")

    assert response.status_code == 200
    assert response.json()["commit_sha"] == "a1b2c3d4e5f6"
