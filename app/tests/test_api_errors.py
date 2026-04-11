from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_root_route_returns_online_status():
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["summary"] == "SpectreMind API online."
    assert body["data"]["docs"] == "/docs"


def test_validation_error_returns_normalized_envelope():
    response = client.post(
        "/chat/ask",
        json={
            "approved": False,
            "session_id": "",
            "session_name": "",
            "latest": False,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
    assert body["summary"] == "Request validation failed."
    assert "errors" in body["data"]


def test_not_found_error_returns_normalized_envelope():
    response = client.get("/tool-runs/999999999")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert "not found" in body["summary"].lower()