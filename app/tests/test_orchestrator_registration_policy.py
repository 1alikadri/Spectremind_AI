from __future__ import annotations

from pathlib import Path

import app.core.orchestrator as orchestrator_module
from app.core.orchestrator import Orchestrator
from app.core.scope import ScopeCheckResult
from app.schemas.tasks import Task
from app.tools.tool_cards import ToolArgument, ToolCard, ToolRegistration


class DummyAether:
    def __init__(self, action: str) -> None:
        self.action = action

    def classify_task(self, objective: str) -> str:
        return "recon"

    def plan(self, task: Task) -> dict:
        return {
            "agent": "AETHER",
            "action": self.action,
            "reason": "policy test",
        }


class DummyTool:
    def run(self, target: str) -> dict:
        return {
            "tool": "dummy",
            "command": "dummy target",
            "stdout": "raw output",
            "stderr": "",
            "returncode": 0,
        }


def _session_path_factory(tmp_path: Path):
    def _get_session_path(session_id: str) -> Path:
        path = tmp_path / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    return _get_session_path


def test_registered_tool_can_complete_without_parser_or_report(monkeypatch, tmp_path):
    monkeypatch.setattr(orchestrator_module, "get_session_path", _session_path_factory(tmp_path))
    monkeypatch.setattr(orchestrator_module, "save_task", lambda task: None)
    monkeypatch.setattr(orchestrator_module, "save_tool_run", lambda **kwargs: 1)
    monkeypatch.setattr(orchestrator_module, "save_findings", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator_module, "save_session_memory", lambda *args, **kwargs: None)
    monkeypatch.setattr(orchestrator_module, "get_session_memory", lambda session_id: None)
    monkeypatch.setattr(
        orchestrator_module,
        "validate_single_target",
        lambda target: ScopeCheckResult(True, "dummy.local", "ok"),
    )

    orchestrator = Orchestrator()
    orchestrator.aether = DummyAether(action="dummy_tool")

    dummy_entry = ToolRegistration(
        card=ToolCard(
            key="dummy_tool",
            display_name="Dummy Tool",
            summary="Policy-only test tool.",
            approval_class="explicit_approval",
            scope_rule="single_target",
            allowed_categories=("recon",),
            arguments=(
                ToolArgument(
                    name="target",
                    kind="target",
                    required=True,
                    description="Single target",
                ),
            ),
        ),
        tool=DummyTool(),
        parser=None,
        stores_findings=False,
        generates_report=False,
        uses_watcher=False,
    )

    monkeypatch.setitem(orchestrator_module.TOOL_REGISTRY, "dummy_tool", dummy_entry)

    result = orchestrator.run_task(
        Task(
            session_id="policy-session",
            objective="run dummy tool",
            target="dummy.local",
            approved=True,
        )
    )

    session_path = tmp_path / "policy-session"

    assert result["status"] == "completed"
    assert result["parsed_result"] is None
    assert result["watcher_result"] is None
    assert result["report"] is None
    assert (session_path / "events.jsonl").exists()