
from __future__ import annotations

from typing import Any

from app.storage.db import (
    get_session_memory as db_get_session_memory,
    save_session_memory as db_save_session_memory,
)


def save_session_memory(session_id: str, data: dict[str, Any]) -> None:
    db_save_session_memory(session_id, data)


def get_session_memory(session_id: str) -> dict[str, Any] | None:
    return db_get_session_memory(session_id)