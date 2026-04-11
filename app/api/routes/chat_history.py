from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.response import api_response
from app.api.session_resolver import resolve_session_id
from app.storage.db import get_chat_messages

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/history")
def get_chat_history(
    session_id: str = "",
    session_name: str = "",
    latest: bool = False,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    resolved = resolve_session_id(
        session_id=session_id,
        session_name=session_name,
        latest=latest,
    )

    if not resolved:
        raise HTTPException(status_code=404, detail="Could not resolve session.")

    messages = get_chat_messages(resolved, limit=limit)

    return api_response(
        status="handled",
        summary=f"{len(messages)} chat message(s) loaded.",
        data={
            "session_id": resolved,
            "messages": messages,
        },
    )