from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WatcherResult(BaseModel):
    agent: Literal["WATCHER"] = "WATCHER"
    observations: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    summary: str = ""
    priority: Literal["low", "medium", "high"] = "low"


class OrchestratorResult(BaseModel):
    status: str
    plan: dict[str, Any] | None = None
    tool_card: dict[str, Any] | None = None
    raw_result: dict[str, Any] | None = None
    parsed_result: dict[str, Any] | None = None
    watcher_result: WatcherResult | None = None
    next_steps: list[str] = Field(default_factory=list)
    report: str | None = None
    message: str | None = None


class CoreResponse(BaseModel):
    agent: Literal["SPECTREMIND"] = "SPECTREMIND"
    status: str
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)
    next_steps: list[str] = Field(default_factory=list)
