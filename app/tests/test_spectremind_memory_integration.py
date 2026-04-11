from __future__ import annotations

from pathlib import Path

from app.core.spectremind_core import SpectreMindCore


class DummyOrchestrator:
    def __init__(self, response: dict):
        self.response = response
        self.last_task = None

    def run_task(self, task):
        self.last_task = task
        return self.response


class DummyMemoryService:
    def __init__(self):
        self.messages: list[dict] = []
        self.states: list[dict] = []

    def add_chat_message(self, session_id: str, role: str, content: str) -> None:
        self.messages.append(
            {
                "session_id": session_id,
                "role": role,
                "content": content,
            }
        )

    def save_session_state(
        self,
        session_id: str,
        current_target: str | None = None,
        current_objective: str | None = None,
        active_hypotheses: list[str] | None = None,
        unresolved_items: list[str] | None = None,
        tool_state: dict | None = None,
        next_steps: list[str] | None = None,
    ) -> None:
        self.states.append(
            {
                "session_id": session_id,
                "current_target": current_target,
                "current_objective": current_objective,
                "active_hypotheses": active_hypotheses or [],
                "unresolved_items": unresolved_items or [],
                "tool_state": tool_state or {},
                "next_steps": next_steps or [],
            }
        )

    def get_session_state(self, session_id: str):
        return {
            "session_id": session_id,
            "current_target": "10.0.0.1",
            "current_objective": "scan 10.0.0.1",
            "active_hypotheses": [],
            "unresolved_items": [],
            "tool_state": {},
            "next_steps": [],
            "updated_at": "2026-04-10T00:00:00+00:00",
        }


def test_handle_operational_persists_chat_messages_and_session_state(monkeypatch):
    core = SpectreMindCore()
    core.orchestrator = DummyOrchestrator(
        {
            "status": "completed",
            "plan": {"action": "run_nmap"},
            "raw_result": {"tool": "nmap", "returncode": 0},
            "parsed_result": {
                "host": "10.0.0.1",
                "host_status": "up",
                "open_ports": [80],
                "filtered_summary": None,
                "port_details": [
                    {"service": "http", "port": 80, "protocol": "tcp", "state": "open", "version": None}
                ],
            },
            "watcher_result": {
                "summary": "HTTP detected.",
                "priority": "medium",
                "suggestions": ["run_http_probe"],
                "unresolved": [],
            },
        }
    )
    core.memory = DummyMemoryService()

    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_by_id",
        lambda session_id: {"session_id": session_id, "name": None, "created_at": "x", "status": "active"},
    )

    result = core.handle(
        text="scan 10.0.0.1",
        approved=True,
        session_id="existing-session-1",
    )

    assert result["status"] == "completed"
    assert len(core.memory.messages) == 2
    assert core.memory.messages[0]["session_id"] == "existing-session-1"
    assert core.memory.messages[0]["role"] == "user"
    assert core.memory.messages[0]["content"] == "scan 10.0.0.1"
    assert core.memory.messages[1]["role"] == "assistant"
    assert "Scan executed." in core.memory.messages[1]["content"]

    assert len(core.memory.states) == 1
    assert core.memory.states[0]["session_id"] == "existing-session-1"
    assert core.memory.states[0]["current_target"] == "10.0.0.1"
    assert core.memory.states[0]["current_objective"] == "scan 10.0.0.1"
    assert core.memory.states[0]["next_steps"] == ["run_http_probe"]


def test_show_report_persists_chat_messages_for_resolved_session(monkeypatch, tmp_path):
    core = SpectreMindCore()
    core.memory = DummyMemoryService()

    report_session_path = tmp_path / "report-session"
    report_session_path.mkdir(parents=True, exist_ok=True)
    (report_session_path / "report.md").write_text("# Report", encoding="utf-8")

    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_by_name",
        lambda name: {"session_id": "report-session", "name": name, "created_at": "x", "status": "active"},
    )
    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_path",
        lambda session_id: report_session_path,
    )

    result = core.handle(text="show report for session alpha")

    assert result["status"] == "handled"
    assert result["summary"] == "Report loaded."
    assert len(core.memory.messages) == 2
    assert core.memory.messages[0]["session_id"] == "report-session"
    assert core.memory.messages[0]["role"] == "user"
    assert core.memory.messages[1]["role"] == "assistant"
    assert "Report loaded." in core.memory.messages[1]["content"]

def test_handle_save_memory_routes_to_memory_service():
    core = SpectreMindCore()
    core.memory = DummyMemoryService()
    saved = {"called": False, "args": None}

    def fake_remember(memory_type, content, tags=None, memory_key=None, source_session_id=None):
        saved["called"] = True
        saved["args"] = {
            "memory_type": memory_type,
            "content": content,
            "source_session_id": source_session_id,
        }
        return 101

    core.memory.remember = fake_remember

    result = core.handle(text="remember that HTTP on port 80 usually needs probing")

    assert result["status"] == "handled"
    assert result["summary"] == "Memory saved."
    assert result["data"]["memory_id"] == 101
    assert saved["called"] is True
    assert saved["args"]["memory_type"] == "note"
    assert "HTTP on port 80" in saved["args"]["content"]


def test_handle_recall_memory_returns_memory_results():
    core = SpectreMindCore()
    core.memory = DummyMemoryService()

    def fake_recall(query="", limit=8, memory_type=None):
        return [
            {
                "id": 7,
                "memory_type": "tool_card",
                "memory_key": "http-probe",
                "content": "Probe HTTP after open 80/tcp or http-like service names.",
                "tags": ["service:http"],
                "source_session_id": None,
                "created_at": "2026-04-10T00:00:00+00:00",
                "updated_at": "2026-04-10T00:00:00+00:00",
            }
        ]

    core.memory.recall = fake_recall

    result = core.handle(text="what do you remember about http")

    assert result["status"] == "handled"
    assert result["summary"] == "1 memory item(s) loaded."
    assert len(result["data"]["memories"]) == 1
    assert result["data"]["memories"][0]["memory_key"] == "http-probe"