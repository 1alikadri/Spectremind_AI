from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.response import api_response
from app.core.session import get_session_path
from app.storage.db import get_latest_session_id, get_session_by_name
from app.api.schemas import ApiEnvelope, AskRequest
from app.api.session_resolver import resolve_session_id

router = APIRouter(prefix="/reports", tags=["reports"])





@router.get("", response_model=ApiEnvelope)
def get_report(
    session_id: str = "",
    session_name: str = "",
    latest: bool = False,
) -> dict:
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)
    if not resolved:
        raise HTTPException(status_code=404, detail="Could not resolve session.")

    report_path = get_session_path(resolved) / "report.md"
    if not report_path.exists():
        return api_response(
            status="handled",
            summary="Report not found for session.",
            data={
                "session_id": resolved,
                "report_path": str(report_path),
                "report": None,
            },
        )

    return api_response(
        status="handled",
        summary="Report loaded.",
        data={
            "session_id": resolved,
            "report_path": str(report_path),
            "report": report_path.read_text(encoding="utf-8"),
        },
    )