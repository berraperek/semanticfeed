from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version() -> None:
    response = client.get("/api/v1/version")

    assert response.status_code == 200
    assert "version" in response.json()
    assert "debug" in response.json()


def test_root_level_health_removed() -> None:
    assert client.get("/health").status_code == 404
