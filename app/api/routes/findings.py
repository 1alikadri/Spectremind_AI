from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.response import api_response
from app.storage.db import get_findings_by_session, get_latest_session_id, get_session_by_name
from app.api.schemas import ApiEnvelope, AskRequest
from app.api.session_resolver import resolve_session_id

router = APIRouter(prefix="/findings", tags=["findings"])





@router.get("", response_model=ApiEnvelope)
def get_findings(
    session_id: str = "",
    session_name: str = "",
    latest: bool = False,
) -> dict:
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)
    if not resolved:
        raise HTTPException(status_code=404, detail="Could not resolve session.")

    findings = get_findings_by_session(resolved)

    if findings:
        distinct_runs = len({row.get("tool_run_id") for row in findings if row.get("tool_run_id") is not None})
        summary = f"Findings loaded from {distinct_runs} tool run(s)." if distinct_runs else "Findings loaded."
    else:
        summary = "No findings found for session."

    return api_response(
        status="handled",
        summary=summary,
        data={
            "session_id": resolved,
            "findings": findings,
        },
    )
