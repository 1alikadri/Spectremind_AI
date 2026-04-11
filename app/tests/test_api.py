from __future__ import annotations
from app.api.deps import get_core, get_memory
from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health_route_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "spectremind-api"


def test_sessions_route_returns_success(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.sessions.list_sessions",
        lambda limit=10: [
            {
                "session_id": "session-1",
                "name": "alpha",
                "created_at": "2026-04-10T00:00:00+00:00",
                "status": "active",
                "finding_count": 0,
                "tool_run_count": 0,
                "has_memory": 0,
            }
        ],
    )

    response = client.get("/sessions")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert len(body["data"]["sessions"]) == 1
    assert body["data"]["sessions"][0]["session_id"] == "session-1"


def test_create_session_route_returns_created_session(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.sessions.create_session",
        lambda name=None: {
            "session_id": "created-session",
            "name": name,
            "created_at": "2026-04-10T00:00:00+00:00",
            "status": "active",
        },
    )

    response = client.post("/sessions", json={"name": "alpha-api"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["data"]["session_id"] == "created-session"
    assert body["data"]["name"] == "alpha-api"


def test_chat_ask_route_calls_core():
    class DummyCore:
        def handle(self, text, approved=False, session_id="", session_name="", latest=False):
            return {
                "status": "handled",
                "summary": "Mock response.",
                "data": {
                    "echo": text,
                    "approved": approved,
                    "session_id": session_id,
                    "session_name": session_name,
                    "latest": latest,
                },
                "next_steps": [],
            }

    app.dependency_overrides[get_core] = lambda: DummyCore()
    try:
        response = client.post(
            "/chat/ask",
            json={
                "text": "show sessions",
                "approved": False,
                "session_id": "",
                "session_name": "",
                "latest": False,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "handled"
        assert body["data"]["echo"] == "show sessions"
    finally:
        app.dependency_overrides.clear()

def test_memory_save_route_returns_memory_id():
    class DummyMemory:
        def remember(self, memory_type, content, source_session_id=None):
            return 123

    app.dependency_overrides[get_memory] = lambda: DummyMemory()
    try:
        response = client.post(
            "/memory/save",
            json={
                "content": "HTTP on port 80 should trigger probing.",
                "memory_type": "note",
                "session_id": "",
                "session_name": "",
                "latest": False,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "handled"
        assert body["data"]["memory_id"] == 123
    finally:
        app.dependency_overrides.clear()

def test_memory_recall_route_returns_results():
    class DummyMemory:
        def recall(self, query="", limit=8, memory_type=None):
            return [
                {
                    "id": 1,
                    "memory_type": "note",
                    "memory_key": None,
                    "content": "HTTP should be probed.",
                    "tags": ["service:http"],
                    "source_session_id": None,
                    "created_at": "2026-04-10T00:00:00+00:00",
                    "updated_at": "2026-04-10T00:00:00+00:00",
                }
            ]

    app.dependency_overrides[get_memory] = lambda: DummyMemory()
    try:
        response = client.post(
            "/memory/recall",
            json={
                "query": "http",
                "memory_type": None,
                "limit": 8,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "handled"
        assert len(body["data"]["memories"]) == 1
        assert body["data"]["memories"][0]["content"] == "HTTP should be probed."
    finally:
        app.dependency_overrides.clear()

def test_tool_runs_route_returns_runs(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.tool_runs.get_latest_session_id",
        lambda: "session-1",
    )
    monkeypatch.setattr(
        "app.api.routes.tool_runs.get_tool_runs_by_session",
        lambda session_id: [
            {
                "id": 77,
                "session_id": session_id,
                "tool_name": "nmap",
                "command_preview": "nmap -Pn -sV test.local",
                "stdout_path": "stdout.txt",
                "stderr_path": "stderr.txt",
                "returncode": 0,
                "created_at": "2026-04-10T00:00:00+00:00",
            }
        ],
    )

    response = client.get("/tool-runs", params={"latest": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["data"]["tool_runs"][0]["id"] == 77