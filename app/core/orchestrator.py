from app.agents.aether import AetherAgent
from app.agents.scribe import ScribeAgent
from app.tools.registry import TOOL_REGISTRY
from app.parsers.nmap_parser import parse_nmap_output
from app.core.logger import append_event
from app.core.session import get_session_path
from app.core.files import save_text_file
from app.core.scope import validate_single_target
from app.schemas.tasks import Task
from app.storage.db import save_task, save_tool_run, save_findings


class Orchestrator:
    def __init__(self) -> None:
        self.aether = AetherAgent()
        self.scribe = ScribeAgent()

    def run_task(self, task: Task) -> dict:
        session_path = get_session_path(task.session_id)
        log_path = session_path / "events.jsonl"

        task.category = self.aether.classify_task(task.objective)
        save_task(task)
        append_event(log_path, "task_classified", task.model_dump())

        plan = self.aether.plan(task)
        append_event(log_path, "plan_created", plan)

        if plan["action"] == "run_nmap":
            if not task.approved:
                return {
                    "status": "blocked",
                    "reason": "Task requires explicit approval before execution."
                }

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
                return {
                    "status": "blocked",
                    "reason": scope_result.reason,
                }

            tool = TOOL_REGISTRY["run_nmap"]
            raw_result = tool.run(scope_result.normalized_target)
            append_event(log_path, "tool_executed", raw_result)

            stdout_path = session_path / "nmap_stdout.txt"
            stderr_path = session_path / "nmap_stderr.txt"
            save_text_file(stdout_path, raw_result["stdout"])
            save_text_file(stderr_path, raw_result["stderr"])

            save_tool_run(
                session_id=task.session_id,
                tool_name=raw_result["tool"],
                command_preview=raw_result["command"],
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                returncode=raw_result["returncode"],
            )

            if raw_result["returncode"] != 0:
                return {
                    "status": "tool_error",
                    "plan": plan,
                    "raw_result": raw_result,
                    "message": "Tool execution failed."
                }

            parsed = parse_nmap_output(raw_result["stdout"])
            append_event(log_path, "tool_parsed", parsed)

            save_findings(task.session_id, parsed)

            next_steps = self.aether.suggest_next_steps(parsed)
            append_event(log_path, "next_steps_suggested", {"steps": next_steps})

            report = self.scribe.generate_markdown_report(
                session_id=task.session_id,
                objective=task.objective,
                parsed_output=parsed
            )

            return {
                "status": "completed",
                "plan": plan,
                "raw_result": raw_result,
                "parsed_result": parsed,
                "next_steps": next_steps,
                "report": report,
            }

        if plan["action"] == "generate_report_only":
            report = self.scribe.generate_markdown_report(
                session_id=task.session_id,
                objective=task.objective,
                parsed_output={
                    "host": task.target or "Unknown",
                    "open_ports": [],
                    "services": [],
                    "port_details": [],
                    "os_hint": None,
                }
            )

            return {
                "status": "completed",
                "plan": plan,
                "next_steps": [],
                "report": report,
            }

        return {
            "status": "no_execution",
            "plan": plan,
            "message": "No executable action selected."
        }