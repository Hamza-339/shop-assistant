from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_returns_fixed_ok_response():
    response = client.get("/api")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
