from __future__ import annotations

from app.core.intent_router import IntentRouter


def test_router_blocks_run_scan_without_target(monkeypatch):
    router = IntentRouter()

    monkeypatch.setattr(
        router.llm,
        "chat_json",
        lambda system_prompt, user_prompt, temperature=0.0: {
            "action": "run_scan",
            "domain": "OPERATIONAL",
            "use_latest": False,
            "reason": "route to scan",
        },
    )

    result = router.route(
        "check it",
        {
            "target": None,
            "session_name": None,
            "session_id": None,
            "use_latest": False,
            "memory_content": None,
            "memory_query": None,
            "memory_type": None,
        },
    )

    assert result is not None
    assert result.action == "blocked"


def test_router_accepts_show_report_with_latest(monkeypatch):
    router = IntentRouter()

    monkeypatch.setattr(
        router.llm,
        "chat_json",
        lambda system_prompt, user_prompt, temperature=0.0: {
            "action": "show_report",
            "domain": "SYSTEM",
            "use_latest": True,
            "reason": "latest report request",
        },
    )

    result = router.route(
        "pull the latest writeup",
        {
            "target": None,
            "session_name": None,
            "session_id": None,
            "use_latest": False,
            "memory_content": None,
            "memory_query": None,
            "memory_type": None,
        },
    )

    assert result is not None
    assert result.action == "show_report"
    assert result.use_latest is True


def test_router_blocks_session_action_without_selector(monkeypatch):
    router = IntentRouter()

    monkeypatch.setattr(
        router.llm,
        "chat_json",
        lambda system_prompt, user_prompt, temperature=0.0: {
            "action": "show_findings",
            "domain": "SYSTEM",
            "use_latest": False,
            "reason": "findings request",
        },
    )

    result = router.route(
        "show me the findings",
        {
            "target": None,
            "session_name": None,
            "session_id": None,
            "use_latest": False,
            "memory_content": None,
            "memory_query": None,
            "memory_type": None,
        },
    )

    assert result is not None
    assert result.action == "blocked"


def test_router_accepts_recall_memory_when_query_exists(monkeypatch):
    router = IntentRouter()

    monkeypatch.setattr(
        router.llm,
        "chat_json",
        lambda system_prompt, user_prompt, temperature=0.0: {
            "action": "recall_memory",
            "domain": "SYSTEM",
            "use_latest": False,
            "reason": "memory lookup",
        },
    )

    result = router.route(
        "what do we know about ssh",
        {
            "target": None,
            "session_name": None,
            "session_id": None,
            "use_latest": False,
            "memory_content": None,
            "memory_query": "ssh",
            "memory_type": None,
        },
    )

    assert result is not None
    assert result.action == "recall_memory"
    assert result.memory_query == "ssh"