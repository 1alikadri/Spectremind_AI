# tests/test_watcher.py
from app.agents.watcher import WatcherAgent


def test_watcher_suggests_full_port_scan_when_host_up_and_no_open_ports():
    watcher = WatcherAgent()

    parsed_output = {
        "host": "10.10.10.10",
        "host_status": "up",
        "filtered_summary": None,
        "open_ports": [],
        "services": [],
        "port_details": [],
        "os_hint": None,
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {},
        "evidence_count": 0,
    }

    result = watcher.process("session-1", parsed_output)

    assert result["agent"] == "WATCHER"
    assert "run_full_port_scan" in result["suggestions"]
    assert result["priority"] == "medium"


def test_watcher_suggests_udp_scan_and_firewall_analysis_when_filtered_summary_exists():
    watcher = WatcherAgent()

    parsed_output = {
        "host": "10.10.10.20",
        "host_status": "up",
        "filtered_summary": "999 filtered tcp ports (no-response)",
        "open_ports": [],
        "services": [],
        "port_details": [],
        "os_hint": None,
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {"filtered": 999},
        "evidence_count": 0,
    }

    result = watcher.process("session-2", parsed_output)

    assert "run_udp_scan" in result["suggestions"]
    assert "analyze_firewall_rules" in result["suggestions"]
    assert result["priority"] == "high"
    assert result["unresolved"]


def test_watcher_suggests_http_probe_for_port_80():
    watcher = WatcherAgent()

    parsed_output = {
        "host": "web.local",
        "host_status": "up",
        "filtered_summary": None,
        "open_ports": [80],
        "services": ["http"],
        "port_details": [
            {
                "port": 80,
                "protocol": "tcp",
                "state": "open",
                "service": "http",
                "version": "nginx",
            }
        ],
        "os_hint": None,
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {"open": 1},
        "evidence_count": 1,
    }

    result = watcher.process("session-3", parsed_output)

    assert "run_http_probe" in result["suggestions"]
    assert result["priority"] == "medium"


def test_watcher_suggests_http_probe_for_http_service_not_only_port_80():
    watcher = WatcherAgent()

    parsed_output = {
        "host": "web.local",
        "host_status": "up",
        "filtered_summary": None,
        "open_ports": [8080],
        "services": ["http-proxy"],
        "port_details": [
            {
                "port": 8080,
                "protocol": "tcp",
                "state": "open",
                "service": "http-proxy",
                "version": None,
            }
        ],
        "os_hint": None,
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {"open": 1},
        "evidence_count": 1,
    }

    result = watcher.process("session-4", parsed_output)

    assert "run_http_probe" in result["suggestions"]


def test_watcher_suggests_ssh_auth_methods_for_ssh_service():
    watcher = WatcherAgent()

    parsed_output = {
        "host": "ssh.local",
        "host_status": "up",
        "filtered_summary": None,
        "open_ports": [22],
        "services": ["ssh"],
        "port_details": [
            {
                "port": 22,
                "protocol": "tcp",
                "state": "open",
                "service": "ssh",
                "version": "OpenSSH 9.0",
            }
        ],
        "os_hint": "Linux",
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {"open": 1},
        "evidence_count": 1,
    }

    result = watcher.process("session-5", parsed_output)

    assert "check_ssh_auth_methods" in result["suggestions"]


def test_watcher_returns_empty_suggestions_when_no_rules_match():
    watcher = WatcherAgent()

    parsed_output = {
        "host": "db.local",
        "host_status": "up",
        "filtered_summary": None,
        "open_ports": [3306],
        "services": ["mysql"],
        "port_details": [
            {
                "port": 3306,
                "protocol": "tcp",
                "state": "open",
                "service": "mysql",
                "version": "8.0",
            }
        ],
        "os_hint": None,
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {"open": 1},
        "evidence_count": 1,
    }

    result = watcher.process("session-6", parsed_output)

    assert result["suggestions"] == []


def test_watcher_merges_previous_memory_observations_and_tags():
    watcher = WatcherAgent()

    previous_memory = {
        "observations": ["Host: old-host", "Host status: up"],
        "unresolved": ["Older unresolved item"],
        "tags": ["host:up", "ports:none"],
    }

    parsed_output = {
        "host": "new-host",
        "host_status": "up",
        "filtered_summary": None,
        "open_ports": [22],
        "services": ["ssh"],
        "port_details": [
            {
                "port": 22,
                "protocol": "tcp",
                "state": "open",
                "service": "ssh",
                "version": None,
            }
        ],
        "os_hint": None,
        "scan_protocols_seen": ["tcp"],
        "all_port_states": {"open": 1},
        "evidence_count": 1,
    }

    result = watcher.process("session-7", parsed_output, previous_memory=previous_memory)

    assert "Host: old-host" in result["observations"]
    assert "Host: new-host" in result["observations"]
    assert "host:up" in result["tags"]
    assert "service:ssh" in result["tags"]


# tests/test_nmap_parser.py
from app.parsers.nmap_parser import parse_nmap_output


def test_parse_nmap_output_extracts_open_tcp_and_udp_ports():
    raw = """
Starting Nmap 7.94
Nmap scan report for demo.local
Host is up.
Not shown: 998 filtered tcp ports (no-response)
22/tcp open ssh OpenSSH 9.0
80/tcp open http nginx 1.24.0
53/udp open domain
Service Info: OS: Linux
"""

    parsed = parse_nmap_output(raw)

    assert parsed["host"] == "demo.local"
    assert parsed["host_status"] == "up"
    assert parsed["filtered_summary"] == "998 filtered tcp ports (no-response)"
    assert parsed["os_hint"] == "Linux"
    assert parsed["open_ports"] == [22, 53, 80]
    assert parsed["scan_protocols_seen"] == ["tcp", "udp"]
    assert parsed["all_port_states"]["open"] == 3
    assert parsed["evidence_count"] == 3

    assert {"port": 22, "protocol": "tcp", "state": "open", "service": "ssh", "version": "OpenSSH 9.0"} in parsed["port_details"]
    assert {"port": 53, "protocol": "udp", "state": "open", "service": "domain", "version": None} in parsed["port_details"]


def test_parse_nmap_output_tracks_closed_summary():
    raw = """
Nmap scan report for 10.0.0.5
Host is up.
All 1000 scanned ports on 10.0.0.5 are closed
"""

    parsed = parse_nmap_output(raw)

    assert parsed["host"] == "10.0.0.5"
    assert parsed["host_status"] == "up"
    assert parsed["closed_summary"] == "closed"
    assert parsed["open_ports"] == []
    assert parsed["port_details"] == []
    assert parsed["evidence_count"] == 0


def test_parse_nmap_output_counts_non_open_states():
    raw = """
Nmap scan report for host
Host is up.
22/tcp filtered ssh
80/tcp open http
443/tcp closed https
"""

    parsed = parse_nmap_output(raw)

    assert parsed["all_port_states"]["filtered"] == 1
    assert parsed["all_port_states"]["open"] == 1
    assert parsed["all_port_states"]["closed"] == 1
    assert parsed["open_ports"] == [80]
    assert parsed["services"] == ["http"]


def test_parse_nmap_output_handles_host_seems_down():
    raw = """
Nmap scan report for 192.168.1.50
Host seems down.
"""

    parsed = parse_nmap_output(raw)

    assert parsed["host"] == "192.168.1.50"
    assert parsed["host_status"] == "down"
    assert parsed["open_ports"] == []


# tests/test_spectremind_core.py
from app.core.spectremind_core import SpectreMindCore


class DummyOrchestrator:
    def __init__(self, response):
        self.response = response
        self.last_task = None

    def run_task(self, task):
        self.last_task = task
        return self.response


def test_handle_uses_existing_session_id(monkeypatch):
    core = SpectreMindCore()
    dummy = DummyOrchestrator(
        {
            "status": "completed",
            "parsed_result": {
                "host_status": "up",
                "open_ports": [],
                "filtered_summary": None,
                "port_details": [],
            },
            "watcher_result": {
                "summary": "No open ports observed.",
                "priority": "medium",
                "suggestions": ["run_full_port_scan"],
            },
        }
    )
    core.orchestrator = dummy

    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_by_id",
        lambda session_id: {"session_id": session_id, "name": None, "created_at": "x", "status": "active"},
    )

    result = core.handle(
        text="scan 10.0.0.1",
        approved=True,
        session_id="existing-session-1",
    )

    assert dummy.last_task is not None
    assert dummy.last_task.session_id == "existing-session-1"
    assert result["agent"] == "SPECTREMIND"
    assert result["next_steps"] == ["run_full_port_scan"]


def test_handle_reuses_named_session_when_it_exists(monkeypatch):
    core = SpectreMindCore()
    dummy = DummyOrchestrator(
        {
            "status": "completed",
            "parsed_result": {
                "host_status": "up",
                "open_ports": [80],
                "filtered_summary": None,
                "port_details": [
                    {"service": "http", "port": 80, "protocol": "tcp", "state": "open", "version": None}
                ],
            },
            "watcher_result": {
                "summary": "HTTP detected.",
                "priority": "medium",
                "suggestions": ["run_http_probe"],
            },
        }
    )
    core.orchestrator = dummy

    monkeypatch.setattr(
        "app.core.spectremind_core.get_session_by_name",
        lambda name: {"session_id": "named-session-1", "name": name, "created_at": "x", "status": "active"},
    )

    result = core.handle(
        text="scan 10.0.0.2",
        approved=True,
        session_name="engagement-alpha",
    )

    assert dummy.last_task.session_id == "named-session-1"
    assert result["next_steps"] == ["run_http_probe"]


def test_handle_uses_latest_session_when_requested(monkeypatch):
    core = SpectreMindCore()
    dummy = DummyOrchestrator(
        {
            "status": "completed",
            "parsed_result": {
                "host_status": "up",
                "open_ports": [],
                "filtered_summary": "999 filtered tcp ports",
                "port_details": [],
            },
            "watcher_result": {
                "summary": "Filtered responses detected.",
                "priority": "high",
                "suggestions": ["run_full_port_scan", "run_udp_scan", "analyze_firewall_rules"],
            },
        }
    )
    core.orchestrator = dummy

    monkeypatch.setattr(
        "app.core.spectremind_core.get_latest_session_id",
        lambda: "latest-session-1",
    )

    result = core.handle(
        text="scan 10.0.0.3",
        approved=True,
        latest=True,
    )

    assert dummy.last_task.session_id == "latest-session-1"
    assert result["next_steps"] == [
        "run_full_port_scan",
        "run_udp_scan",
        "analyze_firewall_rules",
    ]


def test_handle_creates_named_session_when_missing(monkeypatch):
    core = SpectreMindCore()
    dummy = DummyOrchestrator(
        {
            "status": "completed",
            "parsed_result": {
                "host_status": "up",
                "open_ports": [],
                "filtered_summary": None,
                "port_details": [],
            },
            "watcher_result": {
                "summary": "No open ports observed.",
                "priority": "medium",
                "suggestions": ["run_full_port_scan"],
            },
        }
    )
    core.orchestrator = dummy

    monkeypatch.setattr("app.core.spectremind_core.get_session_by_name", lambda name: None)
    monkeypatch.setattr(
        "app.core.spectremind_core.create_session",
        lambda name=None: {
            "session_id": "created-session-1",
            "name": name,
            "created_at": "x",
            "status": "active",
        },
    )

    result = core.handle(
        text="scan 10.0.0.4",
        approved=True,
        session_name="new-engagement",
    )

    assert dummy.last_task.session_id == "created-session-1"
    assert result["next_steps"] == ["run_full_port_scan"]


def test_handle_returns_blocked_when_session_id_does_not_exist(monkeypatch):
    core = SpectreMindCore()
    monkeypatch.setattr("app.core.spectremind_core.get_session_by_id", lambda session_id: None)

    result = core.handle(
        text="scan 10.0.0.5",
        approved=True,
        session_id="missing-session",
    )

    assert result["status"] == "blocked"
    assert "does not exist" in result["summary"]


def test_handle_returns_blocked_when_latest_session_missing(monkeypatch):
    core = SpectreMindCore()
    monkeypatch.setattr("app.core.spectremind_core.get_latest_session_id", lambda: None)

    result = core.handle(
        text="scan 10.0.0.6",
        approved=True,
        latest=True,
    )

    assert result["status"] == "blocked"
    assert "No latest session is available." == result["summary"]


def test_handle_surfaces_only_relevant_medium_priority_suggestions():
    core = SpectreMindCore()
    core.orchestrator = DummyOrchestrator(
        {
            "status": "completed",
            "parsed_result": {
                "host_status": "up",
                "open_ports": [22],
                "filtered_summary": None,
                "port_details": [
                    {"service": "ssh", "port": 22, "protocol": "tcp", "state": "open", "version": None}
                ],
            },
            "watcher_result": {
                "summary": "SSH detected.",
                "priority": "medium",
                "suggestions": ["check_ssh_auth_methods", "run_http_probe"],
            },
        }
    )

    result = core.handle(
        text="scan 10.0.0.7",
        approved=True,
        session_name="medium-priority-filtering",
    )

    assert result["next_steps"] == ["check_ssh_auth_methods"]
    assert result["agent"] == "SPECTREMIND"