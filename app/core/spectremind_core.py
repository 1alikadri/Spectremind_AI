from __future__ import annotations

from app.core.intent_parser import parse_intent
from app.core.orchestrator import Orchestrator
from app.core.session import create_session, get_session_path
from app.core.session_memory import get_session_memory
from app.schemas.intents import IntentResult
from app.schemas.responses import CoreResponse
from app.schemas.tasks import Task
from app.storage.db import (
    get_findings_by_session,
    get_latest_session_id,
    get_session_by_id,
    get_session_by_name,
    get_tool_runs_by_session,
    list_sessions,
)
from app.core.memory_service import MemoryService


class SpectreMindCore:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.memory = MemoryService()

    def handle(
        self,
        text: str,
        approved: bool = False,
        session_id: str = "",
        session_name: str = "",
        latest: bool = False,
    ) -> dict:
        intent: IntentResult = parse_intent(text)

        if intent.action == "blocked":
            return self._response(status="blocked", summary=intent.reason)

        if intent.action == "unknown":
            return self._response(status="unknown", summary="Request not understood.")

        if intent.action == "run_scan":
            return self._handle_operational(
                intent=intent,
                original_text=text,
                approved=approved,
                session_id=session_id,
                session_name=session_name,
                latest=latest,
            )

        if intent.action in {"save_memory", "recall_memory"}:
            return self._handle_memory(
                intent=intent,
                original_text=text,
            )

        if intent.action in {
            "create_session",
            "show_findings",
            "show_tool_runs",
            "list_sessions",
            "show_session",
            "show_report",
            "show_artifacts",
        }:
            return self._handle_system(
                intent=intent,
                original_text=text,
                latest=latest,
                session_id=session_id,
                session_name=session_name,
            )

        return self._response(status="unsupported", summary="Intent not yet supported.")

    def _handle_operational(
        self,
        intent: IntentResult,
        original_text: str,
        approved: bool,
        session_id: str = "",
        session_name: str = "",
        latest: bool = False,
    ) -> dict:
        try:
            task = self._build_task(
                intent=intent,
                approved=approved,
                session_id=session_id,
                session_name=session_name,
                latest=latest,
            )
        except ValueError as exc:
            return self._response(status="blocked", summary=str(exc))

        self._safe_add_chat_message(task.session_id, "user", original_text)

        result = self.orchestrator.run_task(task)
        surfaced_watcher_suggestions = self._select_watcher_suggestions(result)

        response_data = {
            "session_id": task.session_id,
            **result,
        }

        response = self._response(
            status=result.get("status", "unknown"),
            summary=self._build_operational_summary(result),
            data=response_data,
            next_steps=surfaced_watcher_suggestions,
        )

        watcher_result = result.get("watcher_result") or {}
        raw_result = result.get("raw_result") or {}

        try:
            self.memory.save_session_state(
                session_id=task.session_id,
                current_target=task.target or (result.get("parsed_result") or {}).get("host"),
                current_objective=task.objective,
                active_hypotheses=[],
                unresolved_items=watcher_result.get("unresolved", []),
                tool_state={
                    "last_action": (result.get("plan") or {}).get("action"),
                    "last_status": result.get("status"),
                    "last_tool": raw_result.get("tool"),
                    "last_returncode": raw_result.get("returncode"),
                },
                next_steps=surfaced_watcher_suggestions,
            )
        except Exception:
            pass

        self._safe_add_chat_message(
            task.session_id,
            "assistant",
            self._assistant_chat_text(response),
            metadata={
                "status": response.get("status"),
                "summary": response.get("summary"),
                "next_steps": response.get("next_steps", []),
                "data": response.get("data", {}),
            },
        )

        return response

    def _handle_memory(self, intent: IntentResult, original_text: str) -> dict:
        source_session_id = None

        try:
            if intent.session_id or intent.session_name or intent.use_latest:
                source_session_id = self._resolve_existing_session_id(intent)
        except ValueError as exc:
            return self._response(status="blocked", summary=str(exc))

        if intent.action == "save_memory":
            content = (intent.memory_content or "").strip()
            if not content:
                return self._response(status="blocked", summary="Memory content is required.")

            memory_id = self.memory.remember(
                memory_type=intent.memory_type or "note",
                content=content,
                source_session_id=source_session_id,
            )

            response = self._response(
                status="handled",
                summary="Memory saved.",
                data={
                    "memory_id": memory_id,
                    "memory_type": intent.memory_type or "note",
                    "content": content,
                    "source_session_id": source_session_id,
                },
                next_steps=[],
            )

            self._safe_add_chat_message(source_session_id, "user", original_text)
            self._safe_add_chat_message(
                source_session_id,
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )
            return response

        results = self.memory.recall(
            query=intent.memory_query or "",
            limit=8,
            memory_type=intent.memory_type,
        )

        response = self._response(
            status="handled",
            summary=f"{len(results)} memory item(s) loaded.",
            data={
                "query": intent.memory_query or "",
                "memories": results,
            },
            next_steps=[],
        )

        self._safe_add_chat_message(source_session_id, "user", original_text)
        self._safe_add_chat_message(
            source_session_id,
            "assistant",
            self._assistant_chat_text(response),
            metadata={
                "status": response.get("status"),
                "summary": response.get("summary"),
                "next_steps": response.get("next_steps", []),
                "data": response.get("data", {}),
            },
        )
        return response

    def _handle_system(
        self,
        intent: IntentResult,
        original_text: str,
        latest: bool = False,
        session_id: str = "",
        session_name: str = "",
    ) -> dict:
        if intent.action == "create_session":
            session = create_session(name=intent.session_name or None)
            response = self._response(
                status="handled",
                summary="Session created.",
                data=session,
                next_steps=[],
            )
            self._safe_add_chat_message(session["session_id"], "user", original_text)
            self._safe_add_chat_message(
                session["session_id"],
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )
            return response

        if intent.action == "list_sessions":
            sessions = list_sessions(limit=10)
            return self._response(
                status="handled",
                summary=f"{len(sessions)} session(s) found.",
                data={"sessions": sessions},
                next_steps=[],
            )

        effective_intent = intent.model_copy(
            update={
                "use_latest": intent.use_latest or latest,
                "session_id": intent.session_id or session_id or None,
                "session_name": intent.session_name or session_name or None,
            }
        )

        try:
            resolved_session_id = self._resolve_existing_session_id(effective_intent)
        except ValueError as exc:
            return self._response(status="blocked", summary=str(exc))

        if intent.action == "show_findings":
            findings = get_findings_by_session(resolved_session_id)

            if findings:
                distinct_runs = len(
                    {row.get("tool_run_id") for row in findings if row.get("tool_run_id") is not None}
                )
                if distinct_runs:
                    summary = f"Findings loaded from {distinct_runs} tool run(s)."
                else:
                    summary = "Findings loaded."
            else:
                summary = "No findings found for session."

            response = self._response(
                status="handled",
                summary=summary,
                data={
                    "session_id": resolved_session_id,
                    "findings": findings,
                },
                next_steps=[],
            )
            self._safe_add_chat_message(resolved_session_id, "user", original_text)
            self._safe_add_chat_message(
                resolved_session_id,
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )
            return response

        if intent.action == "show_tool_runs":
            tool_runs = get_tool_runs_by_session(resolved_session_id)

            if tool_runs:
                summary = f"{len(tool_runs)} tool run(s) loaded."
            else:
                summary = "No tool runs found for session."

            response = self._response(
                status="handled",
                summary=summary,
                data={
                    "session_id": resolved_session_id,
                    "tool_runs": tool_runs,
                },
                next_steps=[],
            )
            self._safe_add_chat_message(resolved_session_id, "user", original_text)
            self._safe_add_chat_message(
                resolved_session_id,
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )            
            return response

        if intent.action == "show_session":
            session = get_session_by_id(resolved_session_id)
            session_path = get_session_path(resolved_session_id)
            memory = get_session_memory(resolved_session_id)
            state = self.memory.get_session_state(resolved_session_id)

            response = self._response(
                status="handled",
                summary="Session details loaded.",
                data={
                    "session_id": resolved_session_id,
                    "session": session,
                    "memory": memory,
                    "session_state": state,
                    "artifacts": {
                        "session_path": str(session_path),
                        "report": str(session_path / "report.md"),
                        "stdout": str(session_path / "nmap_stdout.txt"),
                        "stderr": str(session_path / "nmap_stderr.txt"),
                        "events": str(session_path / "events.jsonl"),
                    },
                },
                next_steps=[],
            )
            self._safe_add_chat_message(resolved_session_id, "user", original_text)
            self._safe_add_chat_message(
                resolved_session_id,
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )            
            return response

        if intent.action == "show_report":
            report_path = get_session_path(resolved_session_id) / "report.md"
            if not report_path.exists():
                response = self._response(
                    status="handled",
                    summary="Report not found for session.",
                    data={
                        "session_id": resolved_session_id,
                        "report_path": str(report_path),
                        "report": None,
                    },
                    next_steps=[],
                )
                self._safe_add_chat_message(resolved_session_id, "user", original_text)
                self._safe_add_chat_message(
                    resolved_session_id,
                    "assistant",
                    self._assistant_chat_text(response),
                    metadata={
                        "status": response.get("status"),
                        "summary": response.get("summary"),
                        "next_steps": response.get("next_steps", []),
                        "data": response.get("data", {}),
                    },
                )                
                return response

            response = self._response(
                status="handled",
                summary="Report loaded.",
                data={
                    "session_id": resolved_session_id,
                    "report_path": str(report_path),
                    "report": report_path.read_text(encoding="utf-8"),
                },
                next_steps=[],
            )
            self._safe_add_chat_message(resolved_session_id, "user", original_text)
            self._safe_add_chat_message(
                resolved_session_id,
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )            
            return response

        if intent.action == "show_artifacts":
            session_path = get_session_path(resolved_session_id)
            artifact_paths = {
                "session": session_path,
                "report": session_path / "report.md",
                "stdout": session_path / "nmap_stdout.txt",
                "stderr": session_path / "nmap_stderr.txt",
                "events": session_path / "events.jsonl",
            }

            response = self._response(
                status="handled",
                summary="Artifacts loaded.",
                data={
                    "session_id": resolved_session_id,
                    "artifacts": {
                        label: str(path) if path.exists() else None
                        for label, path in artifact_paths.items()
                    },
                },
                next_steps=[],
            )
            self._safe_add_chat_message(resolved_session_id, "user", original_text)
            self._safe_add_chat_message(
                resolved_session_id,
                "assistant",
                self._assistant_chat_text(response),
                metadata={
                    "status": response.get("status"),
                    "summary": response.get("summary"),
                    "next_steps": response.get("next_steps", []),
                    "data": response.get("data", {}),
                },
            )           
            return response

        return self._response(status="unsupported", summary="System action not implemented.")

    def _build_task(
        self,
        intent: IntentResult,
        approved: bool,
        session_id: str = "",
        session_name: str = "",
        latest: bool = False,
    ) -> Task:
        resolved_session_id = self._resolve_or_create_session_id(
            intent=intent,
            session_id=session_id,
            session_name=session_name,
            latest=latest,
        )

        return Task(
            session_id=resolved_session_id,
            objective=intent.objective or "Scan task",
            target=intent.target,
            approved=approved,
        )

    def _resolve_or_create_session_id(
        self,
        intent: IntentResult,
        session_id: str = "",
        session_name: str = "",
        latest: bool = False,
    ) -> str:
        if session_id:
            existing = get_session_by_id(session_id)
            if not existing:
                raise ValueError("Provided session_id does not exist.")
            return session_id

        if latest or intent.use_latest:
            latest_session_id = get_latest_session_id()
            if not latest_session_id:
                raise ValueError("No latest session is available.")
            return latest_session_id

        requested_name = session_name or intent.session_name or ""
        if requested_name:
            existing = get_session_by_name(requested_name)
            if existing:
                return existing["session_id"]

            session = create_session(name=requested_name)
            return session["session_id"]

        session = create_session(name=None)
        return session["session_id"]

    def _resolve_existing_session_id(self, intent: IntentResult) -> str:
        if intent.session_id:
            existing = get_session_by_id(intent.session_id)
            if not existing:
                raise ValueError("Provided session_id does not exist.")
            return intent.session_id

        if intent.use_latest:
            latest_session_id = get_latest_session_id()
            if not latest_session_id:
                raise ValueError("No latest session is available.")
            return latest_session_id

        if intent.session_name:
            existing = get_session_by_name(intent.session_name)
            if not existing:
                raise ValueError("Provided session name does not exist.")
            return existing["session_id"]

        raise ValueError("System request requires a session selector or 'latest'.")

    def _select_watcher_suggestions(self, result: dict) -> list[str]:
        if result.get("status") != "completed":
            return []

        watcher_result = result.get("watcher_result") or {}
        suggestions = watcher_result.get("suggestions", [])
        priority = watcher_result.get("priority", "low")
        parsed_result = result.get("parsed_result") or {}

        if not suggestions:
            return []

        if priority == "high":
            return suggestions

        return [
            suggestion
            for suggestion in suggestions
            if self._is_relevant_watcher_suggestion(suggestion, parsed_result)
        ]

    def _is_relevant_watcher_suggestion(self, suggestion: str, parsed_result: dict) -> bool:
        open_ports = parsed_result.get("open_ports", []) or []
        host_status = (parsed_result.get("host_status") or "").lower()
        filtered_summary = parsed_result.get("filtered_summary")
        services = [
            str(item.get("service") or "").lower()
            for item in (parsed_result.get("port_details", []) or [])
        ]

        if suggestion == "run_full_port_scan":
            return host_status == "up" and not open_ports

        if suggestion == "run_udp_scan":
            return bool(filtered_summary)

        if suggestion == "analyze_firewall_rules":
            return bool(filtered_summary)

        if suggestion == "run_http_probe":
            return 80 in open_ports or any("http" in service for service in services)

        if suggestion == "check_ssh_auth_methods":
            return any("ssh" in service for service in services)

        return False

    def _build_operational_summary(self, result: dict) -> str:
        if result.get("status") != "completed":
            return result.get("message", "Task handled.")

        watcher_result = result.get("watcher_result") or {}
        if watcher_result.get("priority") == "high" and watcher_result.get("suggestions"):
            return "Scan executed. High-priority follow-up suggestions are available."

        if watcher_result.get("summary"):
            return f"Scan executed. {watcher_result['summary']}"

        return "Scan executed."

    def _safe_add_chat_message(
        self,
        session_id: str | None,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        if not session_id or not str(content).strip():
            return

        try:
            self.memory.add_chat_message(
                session_id=session_id,
                role=role,
                content=content.strip(),
                metadata=metadata or {},
            )
        except Exception as exc:
            print(f"[chat-save-error] role={role} session_id={session_id} error={exc}")
            return

    def _assistant_chat_text(self, response: dict) -> str:
        parts = [response.get("summary", "").strip()]

        next_steps = response.get("next_steps") or []
        if next_steps:
            parts.append(f"Next steps: {', '.join(next_steps)}")

        return "\n".join(part for part in parts if part)

    def _response(
        self,
        status: str,
        summary: str,
        data: dict | None = None,
        next_steps: list[str] | None = None,
    ) -> dict:
        return CoreResponse(
            status=status,
            summary=summary,
            data=data or {},
            next_steps=next_steps or [],
        ).model_dump()