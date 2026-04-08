from pydantic import BaseModel
from typing import Literal, Optional


class IntentResult(BaseModel):
    action: Literal[
        "create_session",
        "run_scan",
        "show_findings",
        "list_sessions",
        "show_session",
        "show_report",
        "show_artifacts",
        "unknown",
        "blocked",
    ]
    target: Optional[str] = None
    objective: Optional[str] = None
    session_name: Optional[str] = None
    session_id: Optional[str] = None
    use_latest: bool = False
    reason: str