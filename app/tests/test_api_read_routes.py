from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.deps import get_memory
from app.api.main import app

client = TestClient(app)


def test_findings_route_returns_results(monkeypatch):
    monkeypatch.setattr("app.api.routes.findings.get_latest_session_id", lambda: "session-1")
    monkeypatch.setattr(
        "app.api.routes.findings.get_findings_by_session",
        lambda session_id: [
            {
                "task_id": "task-1",
                "tool_run_id": 77,
                "host": "test.local",
                "port": 80,
                "protocol": "tcp",
                "state": "open",
                "service": "http",
                "version": "nginx",
                "os_hint": "Linux",
                "created_at": "2026-04-10T00:00:00+00:00",
            }
        ],
    )

    response = client.get("/findings", params={"latest": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["data"]["findings"][0]["tool_run_id"] == 77


def test_reports_route_returns_report(monkeypatch, tmp_path):
    report_dir = tmp_path / "session-1"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "report.md"
    report_path.write_text("# Report", encoding="utf-8")

    monkeypatch.setattr("app.api.routes.reports.get_latest_session_id", lambda: "session-1")
    monkeypatch.setattr("app.api.routes.reports.get_session_path", lambda session_id: report_dir)

    response = client.get("/reports", params={"latest": "true"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["data"]["report"] == "# Report"


def test_sessions_show_route_returns_session_details(monkeypatch, tmp_path):
    class DummyMemory:
        def get_session_state(self, session_id: str):
            return None

    session_dir = tmp_path / "session-1"
    session_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("app.api.session_resolver.get_latest_session_id", lambda: "session-1")
    monkeypatch.setattr(
        "app.api.routes.sessions.get_session_by_id",
        lambda session_id: {
            "session_id": session_id,
            "name": "alpha",
            "created_at": "2026-04-10T00:00:00+00:00",
            "status": "active",
        },
    )
    monkeypatch.setattr("app.api.routes.sessions.get_session_path", lambda session_id: session_dir)
    monkeypatch.setattr("app.api.routes.sessions.get_session_memory", lambda session_id: None)

    app.dependency_overrides[get_memory] = lambda: DummyMemory()
    try:
        response = client.get("/sessions/show", params={"latest": "true"})

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "handled"
        assert body["data"]["session"]["session_id"] == "session-1"
    finally:
        app.dependency_overrides.clear()


def test_tool_run_show_route_returns_single_run(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.tool_runs.get_tool_run_by_id",
        lambda run_id: {
            "id": run_id,
            "session_id": "session-1",
            "tool_name": "nmap",
            "command_preview": "nmap -Pn -sV test.local",
            "stdout_path": "stdout.txt",
            "stderr_path": "stderr.txt",
            "returncode": 0,
            "created_at": "2026-04-10T00:00:00+00:00",
        },
    )

    response = client.get("/tool-runs/77")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["data"]["tool_run"]["id"] == 77


def test_task_show_route_returns_single_task(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.tool_runs.get_task_by_id",
        lambda task_id: {
            "id": task_id,
            "session_id": "session-1",
            "objective": "scan test.local",
            "target": "test.local",
            "category": "recon",
            "approved": 1,
            "created_at": "2026-04-10T00:00:00+00:00",
        },
    )

    response = client.get("/tool-runs/task/task-123")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "handled"
    assert body["data"]["task"]["id"] == "task-123"