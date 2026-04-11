from __future__ import annotations

from app.storage.db import get_latest_session_id, get_session_by_id, get_session_by_name


def resolve_session_id(session_id: str = "", session_name: str = "", latest: bool = False) -> str:
    if latest:
        return get_latest_session_id() or ""

    if session_id:
        row = get_session_by_id(session_id)
        return row["session_id"] if row else ""

    if session_name:
        row = get_session_by_name(session_name)
        return row["session_id"] if row else ""

    return ""


def resolve_optional_session_id(
    session_id: str = "",
    session_name: str = "",
    latest: bool = False,
) -> str | None:
    resolved = resolve_session_id(
        session_id=session_id,
        session_name=session_name,
        latest=latest,
    )
    return resolved or None