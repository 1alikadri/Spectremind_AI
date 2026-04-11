from __future__ import annotations

import json

from app.config import (
    LLM_API_BASE,
    LLM_CHAT_COMPLETIONS_PATH,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
)
from app.core.llm_client import LocalLLMClient, LocalLLMError
from app.schemas.tasks import Task


ALLOWED_CATEGORIES = {"recon", "reporting", "unknown"}
ALLOWED_ACTIONS = {"run_nmap", "generate_report_only", "manual_review"}
ALLOWED_AGENTS = {"AETHER", "SCRIBE"}


class AetherAgent:
    def __init__(self) -> None:
        self.llm = LocalLLMClient(
            base_url=LLM_API_BASE,
            model=LLM_MODEL,
            timeout=LLM_TIMEOUT_SECONDS,
            chat_completions_path=LLM_CHAT_COMPLETIONS_PATH,
        )

    def classify_task(self, objective: str) -> str:
        text = objective.lower()

        recon_keywords = ["scan", "recon", "enumerate", "nmap", "ports", "service"]
        reporting_keywords = ["report", "summary", "writeup", "document"]

        if any(word in text for word in recon_keywords):
            return "recon"
        if any(word in text for word in reporting_keywords):
            return "reporting"
        return "unknown"

    def _validate_plan(self, plan: dict) -> dict:
        category = str(plan.get("category", "")).strip().lower()
        action = str(plan.get("action", "")).strip()
        agent = str(plan.get("agent", "AETHER")).strip().upper()
        reason = str(plan.get("reason", "LLM-generated plan")).strip() or "LLM-generated plan"

        if category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category from LLM: {category}")

        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"Invalid action from LLM: {action}")

        if agent not in ALLOWED_AGENTS:
            raise ValueError(f"Invalid agent from LLM: {agent}")

        return {
            "agent": agent,
            "category": category,
            "action": action,
            "reason": reason,
        }

    def plan(self, task: Task) -> dict:
        fallback_category = self.classify_task(task.objective)

        system_prompt = """
You are AETHER, the orchestration mind of a local security lab assistant.
Return only valid JSON.
Choose one category from: recon, reporting, unknown
Choose one action from: run_nmap, generate_report_only, manual_review
Choose one agent from: AETHER, SCRIBE
Keep reasoning short.
"""

        user_prompt = f"""
Objective: {task.objective}
Target: {task.target}
Approved: {task.approved}

Return JSON with:
{{
  "category": "...",
  "agent": "AETHER" or "SCRIBE",
  "action": "...",
  "reason": "..."
}}
"""

        try:
            raw = self.llm.chat(system_prompt, user_prompt)
            parsed = json.loads(raw)
            validated = self._validate_plan(parsed)

            task.category = validated["category"]
            return {
                "agent": validated["agent"],
                "action": validated["action"],
                "reason": validated["reason"],
            }

        except (json.JSONDecodeError, ValueError, LocalLLMError):
            task.category = fallback_category

            if task.category == "recon":
                return {
                    "agent": "AETHER",
                    "action": "run_nmap",
                    "reason": "Fallback rule-based recon classification.",
                }

            if task.category == "reporting":
                return {
                    "agent": "SCRIBE",
                    "action": "generate_report_only",
                    "reason": "Fallback rule-based reporting classification.",
                }

            return {
                "agent": "AETHER",
                "action": "manual_review",
                "reason": "Fallback triggered due to unclear task or LLM failure.",
            }