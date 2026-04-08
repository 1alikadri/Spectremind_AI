import re


def parse_nmap_output(output: str) -> dict:
    open_ports = []
    services = []
    port_details = []
    host = None
    os_hint = None
    host_status = None
    filtered_summary = None

    for raw_line in output.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        host_match = re.search(r"Nmap scan report for (.+)", line)
        if host_match:
            host = host_match.group(1).strip()
            continue

        if line.lower() == "host is up.":
            host_status = "up"
            continue

        filtered_match = re.search(r"Not shown:\s*(.+)", line)
        if filtered_match:
            filtered_summary = filtered_match.group(1).strip()
            continue

        os_match = re.search(r"Service Info:\s*OS:\s*([^;]+)", line)
        if os_match:
            os_hint = os_match.group(1).strip()

        if "/tcp" not in line:
            continue

        parts = re.split(r"\s+", line, maxsplit=3)

        if len(parts) < 3:
            continue

        port_proto = parts[0]
        state = parts[1].lower()
        service = parts[2]
        version = parts[3].strip() if len(parts) > 3 else None

        if not port_proto.endswith("/tcp"):
            continue

        if state != "open":
            continue

        try:
            port = int(port_proto.split("/")[0])
        except ValueError:
            continue

        open_ports.append(port)
        services.append(service)
        port_details.append({
            "port": port,
            "protocol": "tcp",
            "state": state,
            "service": service,
            "version": version if version else None,
        })

    return {
        "host": host,
        "host_status": host_status,
        "filtered_summary": filtered_summary,
        "open_ports": open_ports,
        "services": services,
        "port_details": port_details,
        "os_hint": os_hint,
    }