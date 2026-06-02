"""Tests for the Step 1 skeleton: the server starts and reports healthy."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_serves_the_web_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Skin Triage" in response.text


def test_health_is_healthy():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
