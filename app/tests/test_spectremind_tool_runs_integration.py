from __future__ import annotations

from app.core.spectremind_core import SpectreMindCore


def test_show_tool_runs_uses_latest_session_selector(monkeypatch):
    core = SpectreMindCore()

    monkeypatch.setattr(
        "app.core.spectremind_core.get_latest_session_id",
        lambda: "session-1",
    )
    monkeypatch.setattr(
        "app.core.spectremind_core.get_tool_runs_by_session",
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

    result = core.handle("show runs", latest=True)

    assert result["status"] == "handled"
    assert result["summary"] == "1 tool run(s) loaded."
    assert result["data"]["tool_runs"][0]["id"] == 77
    assert result["data"]["tool_runs"][0]["tool_name"] == "nmap"


def test_show_tool_runs_uses_session_name_selector(monkeypatch):
    core = SpectreMindCore()

    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_by_name",
        lambda name: {"session_id": "named-session", "name": name, "created_at": "x", "status": "active"},
    )
    monkeypatch.setattr(
        "app.core.spectremind_core.get_tool_runs_by_session",
        lambda session_id: [
            {
                "id": 12,
                "session_id": session_id,
                "tool_name": "nmap",
                "command_preview": "nmap -Pn -sV named.local",
                "stdout_path": "stdout.txt",
                "stderr_path": "stderr.txt",
                "returncode": 0,
                "created_at": "2026-04-10T00:00:00+00:00",
            }
        ],
    )

    result = core.handle("show runs", session_name="alpha")

    assert result["status"] == "handled"
    assert result["data"]["tool_runs"][0]["session_id"] == "named-session"


def test_show_tool_runs_uses_session_id_selector(monkeypatch):
    core = SpectreMindCore()

    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_by_id",
        lambda session_id: {"session_id": session_id, "name": None, "created_at": "x", "status": "active"},
    )
    monkeypatch.setattr(
        "app.core.spectremind_core.get_tool_runs_by_session",
        lambda session_id: [
            {
                "id": 5,
                "session_id": session_id,
                "tool_name": "nmap",
                "command_preview": "nmap -Pn -sV direct.local",
                "stdout_path": "stdout.txt",
                "stderr_path": "stderr.txt",
                "returncode": 0,
                "created_at": "2026-04-10T00:00:00+00:00",
            }
        ],
    )

    result = core.handle("show runs", session_id="session-direct")

    assert result["status"] == "handled"
    assert result["data"]["tool_runs"][0]["session_id"] == "session-direct"