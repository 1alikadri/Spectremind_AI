from pydantic import BaseModel
from typing import Literal, Optional


class IntentResult(BaseModel):
    action: Literal[
        "create_session",
        "run_scan",
        "show_findings",
        "show_tool_runs",
        "list_sessions",
        "show_session",
        "show_report",
        "show_artifacts",
        "save_memory",
        "recall_memory",
        "unknown",
        "blocked",
    ]

    domain: Optional[Literal[
        "OPERATIONAL",
        "SYSTEM",
        "REPORTING",
        "ENGINEERING",
        "RESEARCH",
        "SOCIAL",
    ]] = None

    target: Optional[str] = None
    objective: Optional[str] = None
    session_name: Optional[str] = None
    session_id: Optional[str] = None
    use_latest: bool = False

    memory_content: Optional[str] = None
    memory_query: Optional[str] = None
    memory_type: Optional[str] = None

    reason: str