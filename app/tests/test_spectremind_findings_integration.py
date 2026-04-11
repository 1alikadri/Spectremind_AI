from __future__ import annotations

from app.core.spectremind_core import SpectreMindCore


def test_show_findings_includes_provenance(monkeypatch):
    core = SpectreMindCore()

    monkeypatch.setattr(
        "app.core.spectremind_core.get_latest_session_id",
        lambda: "session-1",
    )
    monkeypatch.setattr(
        "app.core.spectremind_core.get_findings_by_session",
        lambda session_id: [
            {
                "task_id": "task-123",
                "tool_run_id": 77,
                "host": "test.local",
                "port": 80,
                "protocol": "tcp",
                "state": "open",
                "service": "http",
                "version": "nginx 1.24.0",
                "os_hint": "Linux",
                "created_at": "2026-04-10T00:00:00+00:00",
            }
        ],
    )

    result = core.handle("show findings", latest=True)

    assert result["status"] == "handled"
    assert "tool run" in result["summary"].lower()
    assert result["data"]["findings"][0]["task_id"] == "task-123"
    assert result["data"]["findings"][0]["tool_run_id"] == 77