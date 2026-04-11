from __future__ import annotations

from typing import Any

from app.storage import db


class MemoryService:
    def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        db.save_chat_message(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )

    def get_recent_chat_messages(self, session_id: str, limit: int = 12) -> list[dict]:
        return db.get_chat_messages(session_id=session_id, limit=limit)

    def save_session_state(
        self,
        session_id: str,
        current_target: str | None = None,
        current_objective: str | None = None,
        active_hypotheses: list[str] | None = None,
        unresolved_items: list[str] | None = None,
        tool_state: dict[str, Any] | None = None,
        next_steps: list[str] | None = None,
    ) -> None:
        db.save_session_state(
            session_id=session_id,
            data={
                "current_target": current_target,
                "current_objective": current_objective,
                "active_hypotheses": active_hypotheses or [],
                "unresolved_items": unresolved_items or [],
                "tool_state": tool_state or {},
                "next_steps": next_steps or [],
            },
        )

    def get_session_state(self, session_id: str) -> dict[str, Any] | None:
        return db.get_session_state(session_id)

    def remember(
        self,
        memory_type: str,
        content: str,
        tags: list[str] | None = None,
        memory_key: str | None = None,
        source_session_id: str | None = None,
    ) -> int:
        return db.save_long_term_memory(
            memory_type=memory_type,
            content=content,
            tags=tags,
            memory_key=memory_key,
            source_session_id=source_session_id,
        )

    def recall(
        self,
        query: str = "",
        limit: int = 8,
        memory_type: str | None = None,
    ) -> list[dict]:
        if query.strip():
            return db.search_long_term_memories(
                query=query,
                limit=limit,
                memory_type=memory_type,
            )

        return db.list_long_term_memories(limit=limit, memory_type=memory_type)