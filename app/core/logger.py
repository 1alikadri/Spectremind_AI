from datetime import datetime
from pathlib import Path
import json
from typing import Any


def serialize(obj: Any) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


def append_event(log_path: Path, event_type: str, payload: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "payload": payload,
    }

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=serialize) + "\n")