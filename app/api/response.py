from __future__ import annotations

from typing import Any

from app.api.schemas import ApiEnvelope


def api_response(
    *,
    status: str,
    summary: str,
    data: dict[str, Any] | None = None,
    next_steps: list[str] | None = None,
) -> dict[str, Any]:
    return ApiEnvelope(
        status=status,
        summary=summary,
        data=data or {},
        next_steps=next_steps or [],
    ).model_dump()