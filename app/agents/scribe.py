from datetime import datetime
from app.core.llm_client import LocalLLMClient
from app.config import LLM_BASE_URL, LLM_MODEL


class ScribeAgent:
    def __init__(self) -> None:
        self.llm = LocalLLMClient(base_url=LLM_BASE_URL, model=LLM_MODEL)

    def summarize_findings(self, objective: str, parsed_output: dict) -> str:
        system_prompt = """
You are SCRIBE.
Write a concise operator-facing summary of findings from structured scan data.
Do not invent results.
"""

        user_prompt = f"""
Objective: {objective}

Parsed Output:
{parsed_output}
"""

        try:
            return self.llm.chat(system_prompt, user_prompt)
        except Exception:
            return "LLM summary unavailable. Review structured findings below."

    def generate_markdown_report(self, session_id: str, objective: str, parsed_output: dict) -> str:
        port_details = parsed_output.get("port_details", [])
        host = parsed_output.get("host", "Unknown")
        os_hint = parsed_output.get("os_hint", "Unknown")
        host_status = parsed_output.get("host_status", "unknown")
        filtered_summary = parsed_output.get("filtered_summary", "None")
        summary = self.summarize_findings(objective, parsed_output)

        lines = [
            "# SpectreMind Session Report",
            "",
            f"- Session ID: `{session_id}`",
            f"- Generated: {datetime.utcnow().isoformat()} UTC",
            f"- Objective: {objective}",
            f"- Host: {host}",
            f"- Host Status: {host_status}",
            f"- Filtered Summary: {filtered_summary}",
            f"- OS Hint: {os_hint}",
            "",
            "## Operator Summary",
            "",
            summary,
            "",
            "## Port Findings",
            "",
        ]

        if port_details:
            for item in port_details:
                version_text = f" | Version: {item['version']}" if item.get("version") else ""
                lines.append(
                    f"- {item['port']}/{item['protocol']} | State: {item['state']} | Service: {item['service']}{version_text}"
                )
        else:
            lines.append("- No open ports detected")

        lines.extend([
            "",
            "## Analyst Notes",
            "",
            "- Structured parser output is the source of truth.",
            "- Review raw tool evidence before any further action.",
        ])

        return "\n".join(lines)