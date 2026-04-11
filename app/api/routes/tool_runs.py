from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.response import api_response
from app.storage.db import (
    get_latest_session_id,
    get_session_by_name,
    get_task_by_id,
    get_tool_run_by_id,
    get_tool_runs_by_session,
)
from app.api.schemas import ApiEnvelope, AskRequest
from app.api.session_resolver import resolve_session_id

router = APIRouter(prefix="/tool-runs", tags=["tool-runs"])





@router.get("", response_model=ApiEnvelope)
def list_tool_runs(
    session_id: str = "",
    session_name: str = "",
    latest: bool = False,
) -> dict:
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)
    if not resolved:
        raise HTTPException(status_code=404, detail="Could not resolve session.")

    tool_runs = get_tool_runs_by_session(resolved)
    summary = f"{len(tool_runs)} tool run(s) loaded." if tool_runs else "No tool runs found for session."

    return api_response(
        status="handled",
        summary=summary,
        data={
            "session_id": resolved,
            "tool_runs": tool_runs,
        },
    )


@router.get("/{run_id}", response_model=ApiEnvelope)
def show_tool_run(run_id: int) -> dict:
    row = get_tool_run_by_id(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Tool run not found.")

    return api_response(
        status="handled",
        summary="Tool run loaded.",
        data={"tool_run": row},
    )


@router.get("/task/{task_id}", response_model=ApiEnvelope)
def show_task(task_id: str) -> dict:
    row = get_task_by_id(task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found.")

    return api_response(
        status="handled",
        summary="Task loaded.",
        data={"task": row},
    )