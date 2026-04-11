
from __future__ import annotations

import re


PORT_LINE_RE = re.compile(
    r"^(\d+)\/(tcp|udp)\s+(\S+)\s+(\S+)(?:\s+(.*))?$",
    re.IGNORECASE,
)


def parse_nmap_output(output: str) -> dict:
    open_ports: list[int] = []
    services: list[str] = []
    port_details: list[dict] = []
    host = None
    os_hint = None
    host_status = None
    filtered_summary = None
    closed_summary = None
    scan_protocols_seen: set[str] = set()
    all_port_states: dict[str, int] = {}

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        host_match = re.search(r"^Nmap scan report for (.+)$", line, re.IGNORECASE)
        if host_match:
            host = host_match.group(1).strip()
            continue

        lower = line.lower()

        if lower.startswith("host is up"):
            host_status = "up"
            continue

        if lower.startswith("host seems down"):
            host_status = "down"
            continue

        filtered_match = re.search(r"^Not shown:\s*(.+)$", line, re.IGNORECASE)
        if filtered_match:
            filtered_summary = filtered_match.group(1).strip()
            continue

        closed_match = re.search(
            r"^All\s+\d+\s+scanned ports on .+ are\s+(.+)$",
            line,
            re.IGNORECASE,
        )
        if closed_match:
            closed_summary = closed_match.group(1).strip()
            continue

        os_match = re.search(r"Service Info:\s*OS:\s*([^;]+)", line, re.IGNORECASE)
        if os_match:
            os_hint = os_match.group(1).strip()
            continue

        port_match = PORT_LINE_RE.match(line)
        if not port_match:
            continue

        port = int(port_match.group(1))
        protocol = port_match.group(2).lower()
        state = port_match.group(3).lower()
        service = port_match.group(4).strip()
        version = (port_match.group(5) or "").strip() or None

        scan_protocols_seen.add(protocol)
        all_port_states[state] = all_port_states.get(state, 0) + 1

        if state != "open":
            continue

        open_ports.append(port)
        services.append(service)
        port_details.append(
            {
                "port": port,
                "protocol": protocol,
                "state": state,
                "service": service,
                "version": version,
            }
        )

    return {
        "host": host,
        "host_status": host_status,
        "filtered_summary": filtered_summary,
        "closed_summary": closed_summary,
        "open_ports": sorted(set(open_ports)),
        "services": sorted(set(services)),
        "port_details": port_details,
        "os_hint": os_hint,
        "scan_protocols_seen": sorted(scan_protocols_seen),
        "all_port_states": all_port_states,
        "evidence_count": len(port_details),
    }
