# tests/test_db_session_memory.py
from __future__ import annotations

from app.storage import db


def _init_temp_db(monkeypatch, tmp_path):
    temp_db_path = tmp_path / "spectremind_test.db"
    monkeypatch.setattr(db, "DB_PATH", temp_db_path)
    db.init_db()
    return temp_db_path


def _create_session(session_id: str, name: str | None = None) -> None:
    db.save_session(
        session_id=session_id,
        name=name,
        created_at="2026-04-09T00:00:00+00:00",
        status="active",
    )


def test_get_session_memory_returns_none_when_missing(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)

    result = db.get_session_memory("missing-session")

    assert result is None


def test_save_and_get_session_memory_round_trip(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    session_id = "session-1"
    _create_session(session_id, name="alpha")

    payload = {
        "summary": "Host is up; no open ports observed; 1 follow-up suggestion generated.",
        "observations": [
            "Host: 10.0.0.10",
            "Host status: up",
            "No open ports observed on a responsive host.",
        ],
        "unresolved": [
            "Responsive host has no open ports in current scan results.",
        ],
        "suggestions": [
            "run_full_port_scan",
        ],
        "tags": [
            "host:up",
            "ports:none",
            "protocol:tcp",
        ],
    }

    db.save_session_memory(session_id, payload)
    result = db.get_session_memory(session_id)

    assert result is not None
    assert result["session_id"] == session_id
    assert result["summary"] == payload["summary"]
    assert result["observations"] == payload["observations"]
    assert result["unresolved"] == payload["unresolved"]
    assert result["suggestions"] == payload["suggestions"]
    assert result["tags"] == payload["tags"]
    assert result["updated_at"]


def test_get_session_memory_returns_latest_snapshot_for_session(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    session_id = "session-2"
    _create_session(session_id, name="beta")

    first_payload = {
        "summary": "Initial summary",
        "observations": ["Host: 10.0.0.20"],
        "unresolved": ["Initial unresolved item"],
        "suggestions": ["run_full_port_scan"],
        "tags": ["host:up", "ports:none"],
    }

    second_payload = {
        "summary": "Updated summary",
        "observations": ["Host: 10.0.0.20", "Filtered summary present: 999 filtered tcp ports"],
        "unresolved": ["Filtered responses suggest firewall or packet-filtering controls."],
        "suggestions": ["run_udp_scan", "analyze_firewall_rules"],
        "tags": ["host:up", "signal:filtered"],
    }

    db.save_session_memory(session_id, first_payload)
    db.save_session_memory(session_id, second_payload)
    result = db.get_session_memory(session_id)

    assert result is not None
    assert result["summary"] == second_payload["summary"]
    assert result["observations"] == second_payload["observations"]
    assert result["unresolved"] == second_payload["unresolved"]
    assert result["suggestions"] == second_payload["suggestions"]
    assert result["tags"] == second_payload["tags"]


def test_session_memory_is_isolated_per_session(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)

    session_a = "session-a"
    session_b = "session-b"
    _create_session(session_a, name="alpha")
    _create_session(session_b, name="bravo")

    db.save_session_memory(
        session_a,
        {
            "summary": "Alpha summary",
            "observations": ["Host: 10.0.0.1"],
            "unresolved": [],
            "suggestions": ["run_http_probe"],
            "tags": ["service:http"],
        },
    )
    db.save_session_memory(
        session_b,
        {
            "summary": "Bravo summary",
            "observations": ["Host: 10.0.0.2"],
            "unresolved": ["Responsive host has no open ports in current scan results."],
            "suggestions": ["run_full_port_scan"],
            "tags": ["ports:none"],
        },
    )

    result_a = db.get_session_memory(session_a)
    result_b = db.get_session_memory(session_b)

    assert result_a is not None
    assert result_b is not None
    assert result_a["summary"] == "Alpha summary"
    assert result_b["summary"] == "Bravo summary"
    assert result_a["suggestions"] == ["run_http_probe"]
    assert result_b["suggestions"] == ["run_full_port_scan"]


def test_save_session_memory_defaults_missing_lists_to_empty(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    session_id = "session-3"
    _create_session(session_id)

    db.save_session_memory(
        session_id,
        {
            "summary": "Minimal payload",
        },
    )
    result = db.get_session_memory(session_id)

    assert result is not None
    assert result["summary"] == "Minimal payload"
    assert result["observations"] == []
    assert result["unresolved"] == []
    assert result["suggestions"] == []
    assert result["tags"] == []


def test_save_session_memory_preserves_json_list_content(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    session_id = "session-4"
    _create_session(session_id)

    payload = {
        "summary": "JSON round-trip",
        "observations": ["one", "two", "three"],
        "unresolved": ["needs review"],
        "suggestions": ["run_udp_scan", "analyze_firewall_rules"],
        "tags": ["host:up", "signal:filtered", "protocol:tcp"],
    }

    db.save_session_memory(session_id, payload)
    result = db.get_session_memory(session_id)

    assert result is not None
    assert isinstance(result["observations"], list)
    assert isinstance(result["unresolved"], list)
    assert isinstance(result["suggestions"], list)
    assert isinstance(result["tags"], list)
    assert result["observations"] == ["one", "two", "three"]
    assert result["unresolved"] == ["needs review"]
    assert result["suggestions"] == ["run_udp_scan", "analyze_firewall_rules"]
    assert result["tags"] == ["host:up", "signal:filtered", "protocol:tcp"]