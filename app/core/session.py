# app/core/session.py
from pathlib import Path
from datetime import UTC, datetime
import uuid
import json

from app.config import SESSIONS_DIR
from app.storage.db import save_session


def create_session(name: str | None = None) -> dict:
    session_id = str(uuid.uuid4())
    session_path = SESSIONS_DIR / session_id
    session_path.mkdir(parents=True, exist_ok=True)

    session_data = {
        "session_id": session_id,
        "name": name,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "active",
    }

    with (session_path / "session.json").open("w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)

    save_session(
        session_id=session_data["session_id"],
        name=session_data["name"],
        created_at=session_data["created_at"],
        status=session_data["status"],
    )

    return session_data


def get_session_path(session_id: str) -> Path:
    return SESSIONS_DIR / session_id