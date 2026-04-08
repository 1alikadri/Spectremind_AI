import re
from app.schemas.intents import IntentResult


IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
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


def extract_target(text: str) -> str | None:
    ip_match = IP_RE.search(text)
    if ip_match:
        return ip_match.group(0)

    host_match = HOST_RE.search(text)
    if host_match:
        return host_match.group(0)

    return None


def parse_intent(text: str) -> IntentResult:
    raw = text.strip()
    lower = raw.lower()

    if any(word in lower for word in BLOCKED_WORDS):
        return IntentResult(
            action="blocked",
            reason="Blocked unsafe or disallowed intent."
        )

    if any(x in lower for x in ["list sessions", "show sessions", "recent sessions"]):
        return IntentResult(
            action="list_sessions",
            reason="Matched session listing intent."
        )

    if any(x in lower for x in ["show report", "open report", "latest report"]):
        use_latest = "latest" in lower
        name_match = re.search(r"(?:session called|session named|for session)\s+(.+)$", raw, re.IGNORECASE)
        return IntentResult(
            action="show_report",
            use_latest=use_latest,
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched report lookup intent."
        )

    if any(x in lower for x in ["show artifacts", "artifacts", "show files"]):
        use_latest = "latest" in lower
        name_match = re.search(r"(?:session called|session named|for session)\s+(.+)$", raw, re.IGNORECASE)
        return IntentResult(
            action="show_artifacts",
            use_latest=use_latest,
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched artifact lookup intent."
        )

    if any(x in lower for x in ["show session", "session details", "session info"]):
        use_latest = "latest" in lower
        name_match = re.search(r"(?:session called|session named|for session)\s+(.+)$", raw, re.IGNORECASE)
        return IntentResult(
            action="show_session",
            use_latest=use_latest,
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched session detail intent."
        )

    if any(x in lower for x in ["show findings", "findings", "show ports"]):
        if "latest" in lower:
            return IntentResult(
                action="show_findings",
                use_latest=True,
                reason="Matched findings intent for latest session."
            )

        name_match = re.search(r"(?:session called|session named|for session)\s+(.+)$", raw, re.IGNORECASE)
        return IntentResult(
            action="show_findings",
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched findings intent."
        )

    if any(x in lower for x in ["create session", "new session", "start session"]):
        name_match = re.search(r"(?:called|named)\s+(.+)$", raw, re.IGNORECASE)
        return IntentResult(
            action="create_session",
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched create-session intent."
        )

    if any(x in lower for x in ["scan", "recon", "enumerate", "check target"]):
        target = extract_target(raw)
        name_match = re.search(r"(?:session called|session named|in session)\s+(.+)$", raw, re.IGNORECASE)

        if not target:
            return IntentResult(
                action="blocked",
                reason="Scan request requires a clear single target."
            )

        return IntentResult(
            action="run_scan",
            target=target,
            objective=raw,
            session_name=name_match.group(1).strip() if name_match else None,
            reason="Matched scan intent with valid target."
        )

    return IntentResult(
        action="unknown",
        reason="No supported intent matched."
    )