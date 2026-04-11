from datetime import UTC, datetime

from app.config import (
    LLM_API_BASE,
    LLM_CHAT_COMPLETIONS_PATH,
    LLM_MODEL,
    LLM_TIMEOUT_SECONDS,
)
from app.core.llm_client import LocalLLMClient, LocalLLMError


class ScribeAgent:
    def __init__(self) -> None:
        self.llm = LocalLLMClient(
            base_url=LLM_API_BASE,
            model=LLM_MODEL,
            timeout=LLM_TIMEOUT_SECONDS,
            chat_completions_path=LLM_CHAT_COMPLETIONS_PATH,
        )

    def summarize_findings(self, objective: str, parsed_output: dict) -> str:
        host = parsed_output.get("host") or "Unknown"
        host_status = parsed_output.get("host_status") or "unknown"
        open_ports = parsed_output.get("open_ports", []) or []
        services = parsed_output.get("services", []) or []
        filtered_summary = parsed_output.get("filtered_summary")

        parts = [
            f"Target: {host}",
            f"Host status: {host_status}",
            f"Open ports: {', '.join(map(str, open_ports)) if open_ports else 'none'}",
            f"Services: {', '.join(services) if services else 'none'}",
        ]

        if filtered_summary:
            parts.append(f"Filtered summary: {filtered_summary}")

        return " | ".join(parts)

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
            f"- Generated: {datetime.now(UTC).isoformat()}",
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

        lines.extend(
            [
                "",
                "## Analyst Notes",
                "",
                "- Structured parser output is the source of truth.",
                "- Review raw tool evidence before any further action.",
            ]
        )

        return "\n".join(lines)