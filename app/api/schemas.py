from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class AskRequest(BaseModel):
    text: str
    approved: bool = False
    session_id: str = ""
    session_name: str = ""
    latest: bool = False


class SessionCreateRequest(BaseModel):
    name: str = ""


class MemorySaveRequest(BaseModel):
    content: str
    memory_type: str = "note"
    session_id: str = ""
    session_name: str = ""
    latest: bool = False


class MemoryRecallRequest(BaseModel):
    query: str = ""
    memory_type: str | None = None
    limit: int = Field(default=8, ge=1, le=100)


class ApiEnvelope(BaseModel):
    status: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    next_steps: list[str] = Field(default_factory=list)