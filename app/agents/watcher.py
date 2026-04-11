
from __future__ import annotations

from typing import Any

from app.schemas.responses import WatcherResult


class WatcherAgent:
    name = "WATCHER"

    def process(
        self,
        session_id: str,
        parsed_output: dict[str, Any],
        previous_memory: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        _ = session_id

        current_observations = self._build_observations(parsed_output)
        current_unresolved = self._build_unresolved(parsed_output)
        current_suggestions = self._build_suggestions(parsed_output)
        current_tags = self._build_tags(parsed_output)

        observations = self._merge_unique(
            (previous_memory or {}).get("observations", []),
            current_observations,
            limit=8,
        )
        unresolved = self._merge_unique(
            (previous_memory or {}).get("unresolved", []),
            current_unresolved,
            limit=8,
        )
        tags = self._merge_unique(
            (previous_memory or {}).get("tags", []),
            current_tags,
            limit=12,
        )

        result = WatcherResult(
            observations=observations,
            unresolved=unresolved,
            suggestions=current_suggestions,
            tags=tags,
            summary=self._build_summary(parsed_output, current_suggestions),
            priority=self._determine_priority(parsed_output, current_suggestions),
        )

        return result.model_dump()

    def _build_observations(self, parsed_output: dict[str, Any]) -> list[str]:
        observations: list[str] = []

        host = parsed_output.get("host") or "Unknown host"
        host_status = (parsed_output.get("host_status") or "unknown").lower()
        port_details = parsed_output.get("port_details", []) or []
        filtered_summary = parsed_output.get("filtered_summary")
        protocols = parsed_output.get("scan_protocols_seen", []) or []

        observations.append(f"Host: {host}")
        observations.append(f"Host status: {host_status}")

        if port_details:
            preview = ", ".join(
                f"{item.get('port')}/{item.get('protocol')}"
                for item in port_details[:6]
            )
            suffix = ", ..." if len(port_details) > 6 else ""
            observations.append(
                f"Open ports observed ({len(port_details)}): {preview}{suffix}"
            )
        elif host_status == "up":
            observations.append("No open ports observed on a responsive host.")
        else:
            observations.append("No open ports observed in current results.")

        if protocols:
            observations.append(f"Protocols observed: {', '.join(protocols)}")

        services = parsed_output.get("services", []) or []
        if services:
            service_list = ", ".join(sorted({str(service).lower() for service in services})[:8])
            observations.append(f"Services identified: {service_list}")

        if filtered_summary:
            observations.append(f"Filtered summary present: {filtered_summary}")

        return observations

    def _build_unresolved(self, parsed_output: dict[str, Any]) -> list[str]:
        unresolved: list[str] = []

        host_status = (parsed_output.get("host_status") or "").lower()
        open_ports = parsed_output.get("open_ports", []) or []
        filtered_summary = parsed_output.get("filtered_summary")

        if host_status == "up" and not open_ports:
            unresolved.append("Responsive host has no open ports in current scan results.")

        if filtered_summary:
            unresolved.append("Filtered responses suggest firewall or packet-filtering controls.")

        return unresolved

    def _build_suggestions(self, parsed_output: dict[str, Any]) -> list[str]:
        suggestions: list[str] = []

        host_status = (parsed_output.get("host_status") or "").lower()
        filtered_summary = parsed_output.get("filtered_summary")
        open_ports = parsed_output.get("open_ports", []) or []
        services = [
            str(item.get("service") or "").lower()
            for item in (parsed_output.get("port_details", []) or [])
        ]

        if not open_ports and host_status == "up":
            suggestions.append("run_full_port_scan")

        if filtered_summary:
            suggestions.append("run_udp_scan")
            suggestions.append("analyze_firewall_rules")

        if 80 in open_ports or any("http" in service for service in services):
            suggestions.append("run_http_probe")

        if any("ssh" in service for service in services):
            suggestions.append("check_ssh_auth_methods")

        return self._merge_unique([], suggestions)

    def _build_tags(self, parsed_output: dict[str, Any]) -> list[str]:
        tags: list[str] = []

        host_status = (parsed_output.get("host_status") or "unknown").lower()
        open_ports = parsed_output.get("open_ports", []) or []
        filtered_summary = parsed_output.get("filtered_summary")
        services = [
            str(item.get("service") or "").lower()
            for item in (parsed_output.get("port_details", []) or [])
        ]
        protocols = parsed_output.get("scan_protocols_seen", []) or []

        tags.append(f"host:{host_status}")
        tags.append("ports:none" if not open_ports else "ports:open")

        for protocol in protocols:
            tags.append(f"protocol:{protocol}")

        if filtered_summary:
            tags.append("signal:filtered")

        if 80 in open_ports:
            tags.append("port:80")

        if any("http" in service for service in services):
            tags.append("service:http")

        if any("ssh" in service for service in services):
            tags.append("service:ssh")

        return self._merge_unique([], tags)

    def _build_summary(self, parsed_output: dict[str, Any], suggestions: list[str]) -> str:
        host = parsed_output.get("host") or "Unknown host"
        host_status = (parsed_output.get("host_status") or "unknown").lower()
        port_details = parsed_output.get("port_details", []) or []
        filtered_summary = parsed_output.get("filtered_summary")

        if port_details:
            preview = ", ".join(
                f"{item.get('port')}/{item.get('service') or 'unknown'}"
                for item in port_details[:4]
            )
            port_summary = f"{len(port_details)} open port(s): {preview}"
            if len(port_details) > 4:
                port_summary += ", ..."
        else:
            port_summary = "no open ports observed"

        filtered_text = " filtered responses detected;" if filtered_summary else ""
        suggestion_text = (
            f" {len(suggestions)} follow-up suggestion(s) generated."
            if suggestions
            else " no follow-up suggestions generated."
        )

        return f"{host} is {host_status}; {port_summary};{filtered_text}{suggestion_text}"

    def _determine_priority(self, parsed_output: dict[str, Any], suggestions: list[str]) -> str:
        if parsed_output.get("filtered_summary"):
            return "high"

        if suggestions:
            return "medium"

        return "low"

    def _merge_unique(
        self,
        previous: list[str],
        current: list[str],
        limit: int | None = None,
    ) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []

        for item in [*(previous or []), *(current or [])]:
            value = str(item).strip()
            if not value or value in seen:
                continue
            seen.add(value)
            merged.append(value)

        if limit is not None:
            return merged[-limit:]

        return merged

