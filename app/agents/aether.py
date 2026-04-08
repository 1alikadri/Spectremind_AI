import json

from app.schemas.tasks import Task
from app.core.llm_client import LocalLLMClient
from app.config import LLM_BASE_URL, LLM_MODEL


class AetherAgent:
    def __init__(self) -> None:
        self.llm = LocalLLMClient(base_url=LLM_BASE_URL, model=LLM_MODEL)

    def classify_task(self, objective: str) -> str:
        text = objective.lower()

        recon_keywords = ["scan", "recon", "enumerate", "nmap", "ports", "service"]
        reporting_keywords = ["report", "summary", "writeup", "document"]

        if any(word in text for word in recon_keywords):
            return "recon"
        if any(word in text for word in reporting_keywords):
            return "reporting"
        return "unknown"

    def plan(self, task: Task) -> dict:
        fallback_category = self.classify_task(task.objective)

        system_prompt = """
You are AETHER, the orchestration mind of a local security lab assistant.
Return only valid JSON.
Choose one category from: recon, reporting, unknown
Choose one action from: run_nmap, generate_report_only, manual_review
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
            plan = json.loads(raw)

            if "category" not in plan or "action" not in plan:
                raise ValueError("Missing required keys in LLM plan.")

            task.category = plan["category"]
            return {
                "agent": plan.get("agent", "AETHER"),
                "action": plan["action"],
                "reason": plan.get("reason", "LLM-generated plan"),
            }

        except Exception:
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

    def suggest_next_steps(self, parsed_output: dict) -> list:
        suggestions = []
        port_details = parsed_output.get("port_details", [])
        filtered_summary = (parsed_output.get("filtered_summary") or "").lower()
        host_status = (parsed_output.get("host_status") or "").lower()

        if not port_details:
            if host_status == "up":
                suggestions.append("run_full_port_scan")

            if filtered_summary:
                suggestions.append("run_udp_scan")
                suggestions.append("analyze_firewall_rules")

            return sorted(set(suggestions))

        for port in port_details:
            service = (port.get("service") or "").lower()
            version = (port.get("version") or "").lower()
            combined = f"{service} {version}"

            if "http" in combined:
                suggestions.append("run_http_probe")

            if "ssh" in combined:
                suggestions.append("check_ssh_auth_methods")

            if "smb" in combined or "microsoft-ds" in combined or "netbios" in combined:
                suggestions.append("enumerate_smb")

            if "ftp" in combined:
                suggestions.append("check_ftp_anonymous_access")

            if "mysql" in combined:
                suggestions.append("identify_mysql_exposure")

            if "rdp" in combined or "ms-wbt-server" in combined:
                suggestions.append("inspect_rdp_exposure")

        return sorted(set(suggestions))