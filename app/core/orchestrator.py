from __future__ import annotations

from app.agents.aether import AetherAgent
from app.agents.scribe import ScribeAgent
from app.agents.watcher import WatcherAgent
from app.core.files import save_text_file
from app.core.logger import append_event
from app.core.scope import validate_single_target
from app.core.session import get_session_path
from app.core.session_memory import get_session_memory, save_session_memory
from app.parsers.nmap_parser import parse_nmap_output
from app.reports.markdown import save_markdown_report
from app.schemas.responses import OrchestratorResult, WatcherResult
from app.schemas.tasks import Task
from app.storage.db import save_findings, save_task, save_tool_run
from app.tools.registry import TOOL_REGISTRY


class Orchestrator:
    def __init__(self) -> None:
        self.aether = AetherAgent()
        self.scribe = ScribeAgent()
        self.watcher = WatcherAgent()

    def _get_tool_entry(self, action: str):
        return TOOL_REGISTRY.get(action)

    def _execute_registered_tool(
        self,
        task: Task,
        plan: dict,
        tool_entry,
        session_path,
        log_path,
    ) -> dict:
        tool_card = tool_entry.card

        append_event(
            log_path,
            "tool_selected",
            {
                "tool_key": tool_card.key,
                "display_name": tool_card.display_name,
                "approval_class": tool_card.approval_class,
                "scope_rule": tool_card.scope_rule,
                "allowed_categories": list(tool_card.allowed_categories),
            },
        )

        if task.category not in tool_card.allowed_categories:
            return OrchestratorResult(
                status="blocked",
                plan=plan,
                tool_card=tool_card.to_dict(),
                message="Selected tool is not allowed for the current task category.",
            ).model_dump()

        if tool_card.approval_class == "explicit_approval" and not task.approved:
            return OrchestratorResult(
                status="blocked",
                plan=plan,
                tool_card=tool_card.to_dict(),
                message="Task requires explicit approval before execution.",
            ).model_dump()

        if tool_card.scope_rule != "single_target":
            return OrchestratorResult(
                status="blocked",
                plan=plan,
                tool_card=tool_card.to_dict(),
                message="Unsupported scope rule for selected tool.",
            ).model_dump()

        scope_result = validate_single_target(task.target)
        append_event(
            log_path,
            "scope_checked",
            {
                "allowed": scope_result.allowed,
                "normalized_target": scope_result.normalized_target,
                "reason": scope_result.reason,
            },
        )

        if not scope_result.allowed:
            return OrchestratorResult(
                status="blocked",
                plan=plan,
                tool_card=tool_card.to_dict(),
                message=scope_result.reason,
            ).model_dump()

        raw_result = tool_entry.tool.run(scope_result.normalized_target)
        append_event(
            log_path,
            "tool_executed",
            {
                **raw_result,
                "tool_key": tool_card.key,
            },
        )

        artifact_names = list(tool_card.artifacts) if tool_card.artifacts else []
        stdout_name = artifact_names[0] if len(artifact_names) >= 1 else "nmap_stdout.txt"
        stderr_name = artifact_names[1] if len(artifact_names) >= 2 else "nmap_stderr.txt"

        stdout_path = session_path / stdout_name
        stderr_path = session_path / stderr_name
        save_text_file(stdout_path, raw_result["stdout"])
        save_text_file(stderr_path, raw_result["stderr"])

        tool_run_id = save_tool_run(
            session_id=task.session_id,
            tool_name=raw_result["tool"],
            command_preview=raw_result["command"],
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            returncode=raw_result["returncode"],
        )

        if raw_result["returncode"] != 0:
            return OrchestratorResult(
                status="tool_error",
                plan=plan,
                tool_card=tool_card.to_dict(),
                raw_result=raw_result,
                message="Tool execution failed.",
            ).model_dump()

        parsed: dict | None = None
        if tool_entry.parser is not None:
            parsed = tool_entry.parser(raw_result["stdout"])
            append_event(log_path, "tool_parsed", parsed)

        if parsed and tool_entry.stores_findings:
            save_findings(
                task.session_id,
                parsed,
                task_id=task.id,
                tool_run_id=tool_run_id,
            )

        watcher_result: WatcherResult | None = None
        if parsed and tool_entry.uses_watcher:
            try:
                previous_memory = get_session_memory(task.session_id)
                watcher_payload = self.watcher.process(
                    session_id=task.session_id,
                    parsed_output=parsed,
                    previous_memory=previous_memory,
                )
                watcher_result = WatcherResult(**watcher_payload)
                save_session_memory(task.session_id, watcher_result.model_dump())
                append_event(log_path, "watcher_processed", watcher_result.model_dump())
            except Exception as exc:
                append_event(log_path, "watcher_error", {"error": str(exc)})

        report: str | None = None
        if parsed and tool_entry.generates_report:
            report = self.scribe.generate_markdown_report(
                session_id=task.session_id,
                objective=task.objective,
                parsed_output=parsed,
            )

            report_path = session_path / "report.md"
            save_markdown_report(report_path, report)
            append_event(log_path, "report_saved", {"report_path": str(report_path)})

        next_steps = watcher_result.suggestions if watcher_result else []

        return OrchestratorResult(
            status="completed",
            plan=plan,
            tool_card=tool_card.to_dict(),
            raw_result=raw_result,
            parsed_result=parsed,
            watcher_result=watcher_result,
            next_steps=next_steps,
            report=report,
        ).model_dump()

    def run_task(self, task: Task) -> dict:
        session_path = get_session_path(task.session_id)
        log_path = session_path / "events.jsonl"

        task.category = self.aether.classify_task(task.objective)
        save_task(task)
        append_event(log_path, "task_classified", task.model_dump())

        plan = self.aether.plan(task)
        append_event(log_path, "plan_created", plan)

        tool_entry = self._get_tool_entry(plan["action"])
        if tool_entry is not None:
            return self._execute_registered_tool(task, plan, tool_entry, session_path, log_path)

        if plan["action"] == "generate_report_only":
            report = self.scribe.generate_markdown_report(
                session_id=task.session_id,
                objective=task.objective,
                parsed_output={
                    "host": task.target or "Unknown",
                    "host_status": "unknown",
                    "filtered_summary": None,
                    "closed_summary": None,
                    "open_ports": [],
                    "services": [],
                    "port_details": [],
                    "os_hint": None,
                    "scan_protocols_seen": [],
                    "all_port_states": {},
                    "evidence_count": 0,
                },
            )
            report_path = session_path / "report.md"
            save_markdown_report(report_path, report)
            append_event(log_path, "report_saved", {"report_path": str(report_path)})

            return OrchestratorResult(
                status="completed",
                plan=plan,
                next_steps=[],
                watcher_result=None,
                report=report,
            ).model_dump()

        return OrchestratorResult(
            status="no_execution",
            plan=plan,
            message="No executable action selected.",
        ).model_dump()