from __future__ import annotations

import ipaddress
import re

from app.config import INTENT_ROUTER_ENABLED
from app.core.intent_router import IntentRouter
from app.schemas.intents import IntentResult


IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HOST_RE = re.compile(
    r"\b(?=.{1,253}\b)(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}\b"
)

BLOCKED_WORDS = {
    "hack",
    "exploit",
    "attack",
    "pwn",
    "breach",
    "compromise",
}

LATEST_WORDS = {"latest", "last", "recent", "current"}

ROUTER = IntentRouter() if INTENT_ROUTER_ENABLED else None


def extract_target(text: str) -> str | None:
    ip_match = IPV4_RE.search(text)
    if ip_match:
        return ip_match.group(0)

    for token in re.findall(r"[^\s,;]+", text):
        candidate = token.strip("[](){}<>\"'")
        try:
            ip = ipaddress.ip_address(candidate)
            return str(ip)
        except ValueError:
            pass

    host_match = HOST_RE.search(text)
    if host_match:
        return host_match.group(0)

    return None


def _contains_any_phrase(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _has_latest_marker(lower: str) -> bool:
    tokens = set(re.findall(r"\b[a-z0-9_-]+\b", lower))
    return bool(tokens.intersection(LATEST_WORDS))


def _extract_session_name(raw: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, raw, re.IGNORECASE)
        if match:
            value = match.group(1).strip(" .,:;")
            if value:
                return value
    return None


def _extract_after_prefix(raw: str, prefixes: list[str]) -> str:
    lowered = raw.lower().strip()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return raw[len(prefix):].strip()
    return ""


def _extract_hints(raw: str, lower: str) -> dict:
    session_name = _extract_session_name(
        raw,
        [
            r"(?:session called|session named|for session|of session|in session)\s+(.+)$",
            r"(?:engagement called|engagement named|for engagement|of engagement|in engagement)\s+(.+)$",
        ],
    )

    save_prefixes = [
        "remember that ",
        "remember ",
        "save this memory ",
        "store this ",
        "store memory ",
        "note that ",
    ]
    recall_prefixes = [
        "recall ",
        "search memory ",
        "what do you remember about ",
        "remember anything about ",
        "what did we note about ",
        "what do we know about ",
        "notes on ",
    ]

    memory_content = None
    if any(lower.startswith(prefix) for prefix in save_prefixes):
        memory_content = _extract_after_prefix(raw, save_prefixes) or None

    memory_query = None
    if any(lower.startswith(prefix) for prefix in recall_prefixes):
        memory_query = _extract_after_prefix(raw, recall_prefixes)

    return {
        "target": extract_target(raw),
        "session_name": session_name,
        "session_id": None,
        "use_latest": _has_latest_marker(lower),
        "memory_content": memory_content,
        "memory_query": memory_query,
        "memory_type": "note" if memory_content else None,
    }


def _hard_block(lower: str) -> IntentResult | None:
    if any(re.search(rf"\b{re.escape(word)}\b", lower) for word in BLOCKED_WORDS):
        return IntentResult(
            action="blocked",
            domain="SYSTEM",
            reason=(
                "Use bounded operational language. Rephrase with a clear single target, "
                "for example: 'scan 127.0.0.1', 'enumerate services on example.com', "
                "or 'show findings for session alpha'."
            ),
        )
    return None


def _rule_parse_intent(raw: str, lower: str, hints: dict) -> IntentResult | None:
    if _contains_any_phrase(lower, ["list sessions", "show sessions", "recent sessions"]):
        return IntentResult(
            action="list_sessions",
            domain="SYSTEM",
            reason="Matched session listing intent.",
        )

    if _contains_any_phrase(
        lower,
        [
            "show tool runs",
            "show runs",
            "show executions",
            "show tool history",
            "latest tool runs",
            "latest runs",
            "last runs",
            "recent runs",
            "runs from last session",
            "tool runs from last session",
            "what did we run",
            "what tools did we run",
            "execution history",
            "run history",
        ],
    ):
        return IntentResult(
            action="show_tool_runs",
            domain="SYSTEM",
            use_latest=hints["use_latest"],
            session_name=hints["session_name"],
            reason="Matched tool-run lookup intent.",
        )
    if _contains_any_phrase(
        lower,
        [
            "show report",
            "open report",
            "latest report",
            "last report",
            "recent report",
            "latest writeup",
            "last writeup",
            "recent writeup",
            "engagement summary",
            "session summary",
            "summarize latest engagement",
            "summarize last engagement",
            "summarize recent engagement",
            "summarize latest session",
            "summarize last session",
            "summarize recent session",
            "show report for session",
            "open report for session",
        ],
    ):
        return IntentResult(
            action="show_report",
            domain="SYSTEM",
            use_latest=hints["use_latest"],
            session_name=hints["session_name"],
            reason="Matched report retrieval intent.",
        )

    if _contains_any_phrase(lower, ["show artifacts", "show files", "latest artifacts", "last artifacts", "recent artifacts"]):
        return IntentResult(
            action="show_artifacts",
            domain="SYSTEM",
            use_latest=hints["use_latest"],
            session_name=hints["session_name"],
            reason="Matched artifact lookup intent.",
        )

    if _contains_any_phrase(
        lower,
        [
            "show session",
            "session details",
            "session info",
            "open session",
            "open last session",
            "open latest session",
            "show current session",
        ],
    ):
        return IntentResult(
            action="show_session",
            domain="SYSTEM",
            use_latest=hints["use_latest"],
            session_name=hints["session_name"],
            reason="Matched session detail intent.",
        )

    if _contains_any_phrase(
        lower,
        [
            "show findings",
            "show ports",
            "latest findings",
            "last findings",
            "recent findings",
            "what did we find",
            "what ports did we find",
            "ports from last run",
            "ports from latest run",
            "findings from last run",
            "findings from latest run",
        ],
    ):
        return IntentResult(
            action="show_findings",
            domain="SYSTEM",
            use_latest=hints["use_latest"],
            session_name=hints["session_name"],
            reason="Matched findings intent.",
        )

    if _contains_any_phrase(lower, ["create session", "new session", "start session", "create engagement", "new engagement"]):
        name_match = re.search(r"(?:called|named)\s+(.+)$", raw, re.IGNORECASE)
        return IntentResult(
            action="create_session",
            domain="SYSTEM",
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched create-session intent.",
        )

    recall_prefixes = [
        "recall ",
        "search memory ",
        "what do you remember about ",
        "remember anything about ",
        "what did we note about ",
        "what do we know about ",
        "notes on ",
    ]
    if any(lower.startswith(prefix) for prefix in recall_prefixes) or lower in {
        "recall",
        "show memory",
        "open memory",
    }:
        return IntentResult(
            action="recall_memory",
            domain="SYSTEM",
            memory_query=hints["memory_query"] or "",
            memory_type=None,
            session_name=hints["session_name"],
            use_latest=hints["use_latest"],
            reason="Matched recall-memory intent.",
        )

    save_prefixes = [
        "remember that ",
        "remember ",
        "save this memory ",
        "store this ",
        "store memory ",
        "note that ",
    ]
    if any(lower.startswith(prefix) for prefix in save_prefixes):
        if not hints["memory_content"]:
            return IntentResult(
                action="blocked",
                domain="SYSTEM",
                reason="Memory save request requires content.",

            )

        return IntentResult(
            action="save_memory",
            domain="SYSTEM",
            memory_content=hints["memory_content"],
            memory_type="note",
            session_name=hints["session_name"],
            use_latest=hints["use_latest"],
            reason="Matched save-memory intent.",
        )

    operational_phrases = [
        "scan",
        "recon",
        "enumerate",
        "check target",
        "probe",
        "look at",
        "inspect",
        "check ",
        "review ",
        "assess ",
        "survey ",
        "examine ",
        "take a look at",
    ]
    if hints["target"] and _contains_any_phrase(lower, operational_phrases):
        return IntentResult(
            action="run_scan",
            domain="OPERATIONAL",
            target=hints["target"],
            objective=raw,
            session_name=hints["session_name"],
            reason="Matched operational intent with valid target.",
        )

    if _contains_any_phrase(lower, operational_phrases) and not hints["target"]:
        return IntentResult(
            action="blocked",
            domain="SYSTEM",
            reason="Scan request requires a clear single target.",
        )

    return None


def parse_intent(text: str) -> IntentResult:
    raw = text.strip()
    lower = raw.lower()

    if not raw:
        return IntentResult(
            action="unknown",
            domain="SYSTEM",
            reason="Empty request.",
        )

    blocked = _hard_block(lower)
    if blocked:
        return blocked

    hints = _extract_hints(raw, lower)

    by_rule = _rule_parse_intent(raw, lower, hints)
    if by_rule:
        return by_rule

    if ROUTER is not None:
        routed = ROUTER.route(raw, hints)
        if routed:
            return routed

    return IntentResult(
        action="unknown",
        domain="SYSTEM",
        reason="No supported intent matched.",
    )