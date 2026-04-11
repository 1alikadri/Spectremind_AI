from __future__ import annotations

from app.core.memory_service import MemoryService
from app.storage import db


def _init_temp_db(monkeypatch, tmp_path):
    temp_db_path = tmp_path / "spectremind_memory_test.db"
    monkeypatch.setattr(db, "DB_PATH", temp_db_path)
    db.init_db()
    return temp_db_path


def _create_session(session_id: str, name: str | None = None) -> None:
    db.save_session(
        session_id=session_id,
        name=name,
        created_at="2026-04-10T00:00:00+00:00",
        status="active",
    )


def test_memory_service_chat_messages_round_trip(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    _create_session("session-chat", "alpha")

    service = MemoryService()
    service.add_chat_message("session-chat", "user", "scan 10.0.0.1")
    service.add_chat_message("session-chat", "assistant", "Ready. Approval required.")

    messages = service.get_recent_chat_messages("session-chat", limit=10)

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "scan 10.0.0.1"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Ready. Approval required."


def test_memory_service_session_state_round_trip(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    _create_session("session-state", "bravo")

    service = MemoryService()
    service.save_session_state(
        session_id="session-state",
        current_target="10.0.0.5",
        current_objective="scan 10.0.0.5",
        active_hypotheses=["Host may expose HTTP"],
        unresolved_items=["Need service validation"],
        tool_state={"last_tool": "nmap", "last_status": "completed"},
        next_steps=["run_http_probe"],
    )

    state = service.get_session_state("session-state")

    assert state is not None
    assert state["current_target"] == "10.0.0.5"
    assert state["current_objective"] == "scan 10.0.0.5"
    assert state["active_hypotheses"] == ["Host may expose HTTP"]
    assert state["unresolved_items"] == ["Need service validation"]
    assert state["tool_state"] == {"last_tool": "nmap", "last_status": "completed"}
    assert state["next_steps"] == ["run_http_probe"]


def test_memory_service_recall_matches_long_term_memory_query(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    _create_session("session-memory", "charlie")

    service = MemoryService()
    service.remember(
        memory_type="tool_card",
        memory_key="nmap-http",
        content="Use Nmap service detection for initial HTTP exposure checks.",
        tags=["tool:nmap", "service:http"],
        source_session_id="session-memory",
    )
    service.remember(
        memory_type="playbook",
        memory_key="ssh-followup",
        content="When SSH is open, verify auth methods before deeper action.",
        tags=["service:ssh"],
        source_session_id="session-memory",
    )

    results = service.recall(query="http", limit=10)

    assert len(results) >= 1
    assert any("HTTP" in item["content"] or "http" in item["content"].lower() for item in results)
    assert any("service:http" in item["tags"] for item in results)


def test_memory_service_recall_without_query_returns_recent_memories(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    _create_session("session-recent", "delta")

    service = MemoryService()
    first_id = service.remember(
        memory_type="operator_preference",
        memory_key="tone",
        content="Keep responses concise and tactical.",
        tags=["operator"],
        source_session_id="session-recent",
    )
    second_id = service.remember(
        memory_type="tool_card",
        memory_key="http-probe",
        content="Probe HTTP after open 80/tcp or http-like service names.",
        tags=["service:http"],
        source_session_id="session-recent",
    )

    results = service.recall(limit=10)

    assert len(results) == 2
    assert results[0]["id"] == second_id
    assert results[1]["id"] == first_id