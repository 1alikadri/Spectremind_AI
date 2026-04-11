from __future__ import annotations

import json
from typing import Any

from app.config import (
    INTENT_ROUTER_MODEL,
    INTENT_ROUTER_TIMEOUT_SECONDS,
    LLM_API_BASE,
    LLM_CHAT_COMPLETIONS_PATH,
)
from app.core.llm_client import LocalLLMClient, LocalLLMError
from app.schemas.intents import IntentResult


ALLOWED_ACTIONS = {
    "create_session",
    "show_tool_runs",
    "run_scan",
    "show_findings",
    "list_sessions",
    "show_session",
    "show_report",
    "show_artifacts",
    "save_memory",
    "recall_memory",
    "unknown",
}

ALLOWED_DOMAINS = {
    "OPERATIONAL",
    "SYSTEM",
    "REPORTING",
    "ENGINEERING",
    "RESEARCH",
    "SOCIAL",
}

SESSION_REQUIRED_ACTIONS = {
    "show_findings",
    "show_session",
    "show_report",
    "show_tool_runs",
    "show_artifacts",
}


class IntentRouter:
    def __init__(self) -> None:
        self.llm = LocalLLMClient(
            base_url=LLM_API_BASE,
            model=INTENT_ROUTER_MODEL,
            timeout=INTENT_ROUTER_TIMEOUT_SECONDS,
            chat_completions_path=LLM_CHAT_COMPLETIONS_PATH,
        )

    def route(self, text: str, extracted: dict[str, Any]) -> IntentResult | None:
        system_prompt = """
You are a strict intent router for a local operator-controlled security assistant.

Return JSON only.

Allowed actions:
- create_session
"show_tool_runs",
- run_scan
- show_findings
- list_sessions
- show_session
- show_report
- show_artifacts
- save_memory
- recall_memory
- unknown

Hard rules:
- Never invent a target.
- Never invent a session name.
- Never invent a session id.
- Never invent memory content.
- Never invent memory query.
- Only use extracted hints that are provided.
- Only choose run_scan if extracted_target is present.
- Only choose save_memory if memory_content is present.
- For show_findings/show_tool_runs/show_session/show_report/show_artifacts, require either explicit_latest=true
  or extracted_session_name/session_id.
- If ambiguous, return unknown.

Interpretation hints:
- "latest", "last", "recent", "current" may indicate latest session/report/findings if the phrasing supports it.
- "writeup", "summary", "engagement summary", "report", "notes from latest run" often map to show_report.
- "what did we note about X", "what do you remember about X", "notes on X" often map to recall_memory.
- "open the last session", "show current session", "recent engagement" often map to show_session.
- "what did we find", "ports from last run", "latest findings" often map to show_findings.
- "look at 10.0.0.5", "inspect 10.0.0.5", "check 10.0.0.5", "review 10.0.0.5" can map to run_scan if a real target exists.

Return this schema:
{
  "action": "unknown",
  "domain": "SYSTEM",
  "use_latest": false,
  "reason": "..."
}
""".strip()

        user_prompt = json.dumps(
            {
                "text": text,
                "extracted_target": extracted.get("target"),
                "extracted_session_name": extracted.get("session_name"),
                "extracted_session_id": extracted.get("session_id"),
                "explicit_latest": extracted.get("use_latest", False),
                "memory_content": extracted.get("memory_content"),
                "memory_query": extracted.get("memory_query"),
                "memory_type": extracted.get("memory_type"),
            },
            ensure_ascii=False,
        )

        try:
            payload = self.llm.chat_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
            )
        except LocalLLMError:
            return None

        action = str(payload.get("action", "")).strip()
        if action not in ALLOWED_ACTIONS:
            return None

        domain = str(payload.get("domain", "SYSTEM")).strip().upper() or "SYSTEM"
        if domain not in ALLOWED_DOMAINS:
            domain = "SYSTEM"

        use_latest = bool(payload.get("use_latest", False)) or bool(extracted.get("use_latest", False))
        session_name = extracted.get("session_name")
        session_id = extracted.get("session_id")
        target = extracted.get("target")
        memory_content = extracted.get("memory_content")
        memory_query = extracted.get("memory_query")
        memory_type = extracted.get("memory_type")
        reason = str(payload.get("reason", "")).strip() or "Matched by LLM-assisted router."

        if action == "run_scan" and not target:
            return IntentResult(
                action="blocked",
                domain="SYSTEM",
                reason="Scan request requires a clear single target.",
            )

        if action == "save_memory" and not memory_content:
            return IntentResult(
                action="blocked",
                domain="SYSTEM",
                reason="Memory save request requires content.",
            )

        if action in SESSION_REQUIRED_ACTIONS and not (use_latest or session_name or session_id):
            return IntentResult(
                action="blocked",
                domain="SYSTEM",
                reason="Session request requires a session selector or 'latest'.",
            )

        return IntentResult(
            action=action,
            domain=domain,
            target=target,
            objective=text if action == "run_scan" else None,
            session_name=session_name,
            session_id=session_id,
            use_latest=use_latest,
            memory_content=memory_content,
            memory_query=memory_query,
            memory_type=memory_type,
            reason=reason,
        )