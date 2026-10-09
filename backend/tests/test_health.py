from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


def test_health_returns_ok_envelope():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert body["data"]["service"] == "MediLens API"


def test_unknown_route_returns_clean_error_envelope():
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "not_found"
    # No stack trace or framework text leaks to the user
    assert "Traceback" not in response.text


def test_cors_allows_the_frontend_origin():
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
