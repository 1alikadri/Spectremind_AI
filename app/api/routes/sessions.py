from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_memory
from app.api.response import api_response
from app.api.schemas import SessionCreateRequest
from app.core.memory_service import MemoryService
from app.core.session import create_session, get_session_path
from app.core.session_memory import get_session_memory
from app.storage.db import get_latest_session_id, get_session_by_id, get_session_by_name, list_sessions
from app.api.schemas import ApiEnvelope, AskRequest
from app.api.session_resolver import resolve_session_id

router = APIRouter(prefix="/sessions", tags=["sessions"])





@router.get("", response_model=ApiEnvelope)
def get_sessions(limit: int = Query(default=10, ge=1, le=100)) -> dict:
    sessions = list_sessions(limit=limit)
    return api_response(
        status="handled",
        summary=f"{len(sessions)} session(s) found.",
        data={"sessions": sessions},
    )


@router.post("", response_model=ApiEnvelope)
def create_new_session(request: SessionCreateRequest) -> dict:
    session = create_session(name=request.name or None)
    return api_response(
        status="handled",
        summary="Session created.",
        data=session,
    )


@router.get("/latest", response_model=ApiEnvelope)
def get_latest_session() -> dict:
    latest_session_id = get_latest_session_id()
    if not latest_session_id:
        raise HTTPException(status_code=404, detail="No latest session is available.")

    row = get_session_by_id(latest_session_id)
    return api_response(
        status="handled",
        summary="Latest session loaded.",
        data={"session": row},
    )


@router.get("/show", response_model=ApiEnvelope)
def show_session(
    session_id: str = "",
    session_name: str = "",
    latest: bool = False,
    memory: MemoryService = Depends(get_memory),
) -> dict:
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)
    if not resolved:
        raise HTTPException(status_code=404, detail="Could not resolve session.")

    row = get_session_by_id(resolved)
    if not row:
        raise HTTPException(status_code=404, detail="Session not found.")

    session_path = get_session_path(resolved)
    state = memory.get_session_state(resolved)
    session_memory = get_session_memory(resolved)

    return api_response(
        status="handled",
        summary="Session details loaded.",
        data={
            "session_id": resolved,
            "session": row,
            "memory": session_memory,
            "session_state": state,
            "artifacts": {
                "session_path": str(session_path),
                "report": str(session_path / "report.md"),
                "stdout": str(session_path / "nmap_stdout.txt"),
                "stderr": str(session_path / "nmap_stderr.txt"),
                "events": str(session_path / "events.jsonl"),
            },
        },
    )