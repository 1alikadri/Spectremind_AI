import ipaddress
import re
from dataclasses import dataclass


HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)

BLOCKED_TOKENS = {
    "/",
    "*",
    ",",
    ";",
    "&",
    "|",
    "$(",
    "`",
    " ",
}


@dataclass
class ScopeCheckResult:
    allowed: bool
    normalized_target: str | None
    reason: str


def validate_single_target(target: str | None) -> ScopeCheckResult:
    if not target:
        return ScopeCheckResult(
            allowed=False,
            normalized_target=None,
            reason="Target is required."
        )

    candidate = target.strip()

    if not candidate:
        return ScopeCheckResult(
            allowed=False,
            normalized_target=None,
            reason="Target is empty after trimming."
        )

    for token in BLOCKED_TOKENS:
        if token in candidate:
            return ScopeCheckResult(
                allowed=False,
                normalized_target=None,
                reason=f"Target contains blocked pattern: {token}"
            )

    try:
        ip = ipaddress.ip_address(candidate)
        return ScopeCheckResult(
            allowed=True,
            normalized_target=str(ip),
            reason="Valid single IP target."
        )
    except ValueError:
        pass

    if HOSTNAME_RE.fullmatch(candidate):
        return ScopeCheckResult(
            allowed=True,
            normalized_target=candidate.lower(),
            reason="Valid hostname target."
        )

    return ScopeCheckResult(
        allowed=False,
        normalized_target=None,
        reason="Target must be a single IPv4/IPv6 address or hostname."
    )