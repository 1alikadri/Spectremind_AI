from __future__ import annotations

import app.core.intent_parser as parser_module
from app.schemas.intents import IntentResult


def test_parse_intent_rule_scan_bypasses_router(monkeypatch):
    class ExplodingRouter:
        def route(self, text: str, extracted: dict):
            raise AssertionError("Router should not be called for explicit operational intent.")

    monkeypatch.setattr(parser_module, "ROUTER", ExplodingRouter())

    result = parser_module.parse_intent("inspect 10.0.0.1")

    assert result.action == "run_scan"
    assert result.target == "10.0.0.1"


def test_parse_intent_keeps_hard_block_before_router(monkeypatch):
    class ExplodingRouter:
        def route(self, text: str, extracted: dict):
            raise AssertionError("Router should not be called for blocked language.")

    monkeypatch.setattr(parser_module, "ROUTER", ExplodingRouter())

    result = parser_module.parse_intent("hack 10.0.0.1")

    assert result.action == "blocked"


def test_parse_intent_matches_latest_session_style_phrase():
    result = parser_module.parse_intent("open last session")

    assert result.action == "show_session"
    assert result.use_latest is True


def test_parse_intent_matches_latest_report_style_phrase():
    result = parser_module.parse_intent("summarize latest engagement")

    assert result.action == "show_report"
    assert result.use_latest is True


def test_parse_intent_matches_memory_note_lookup_phrase():
    result = parser_module.parse_intent("what did we note about ssh")

    assert result.action == "recall_memory"
    assert result.memory_query == "ssh"


def test_parse_intent_uses_llm_router_for_ambiguous_allowed_request(monkeypatch):
    class DummyRouter:
        def route(self, text: str, extracted: dict):
            return IntentResult(
                action="show_findings",
                domain="SYSTEM",
                use_latest=True,
                reason="Matched by LLM router.",
            )

    monkeypatch.setattr(parser_module, "ROUTER", DummyRouter())

    result = parser_module.parse_intent("pull up what we found last time")

    assert result.action == "show_findings"
    assert result.use_latest is True


def test_parse_intent_fails_closed_when_router_returns_none(monkeypatch):
    class DummyRouter:
        def route(self, text: str, extracted: dict):
            return None

    monkeypatch.setattr(parser_module, "ROUTER", DummyRouter())

    result = parser_module.parse_intent("pull up whatever we were looking at")

    assert result.action == "unknown"