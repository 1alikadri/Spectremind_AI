from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.storage.models import (
    CREATE_CHAT_MESSAGES_TABLE,
    CREATE_FINDINGS_TABLE,
    CREATE_LONG_TERM_MEMORIES_TABLE,
    CREATE_SESSIONS_TABLE,
    CREATE_SESSION_MEMORY_TABLE,
    CREATE_SESSION_STATE_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_TOOL_RUNS_TABLE,
)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "spectremind.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(CREATE_SESSIONS_TABLE)
        conn.execute(CREATE_TASKS_TABLE)
        conn.execute(CREATE_TOOL_RUNS_TABLE)
        conn.execute(CREATE_FINDINGS_TABLE)
        conn.execute(CREATE_SESSION_MEMORY_TABLE)
        conn.execute(CREATE_CHAT_MESSAGES_TABLE)
        conn.execute(CREATE_SESSION_STATE_TABLE)
        conn.execute(CREATE_LONG_TERM_MEMORIES_TABLE)

        columns = [row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()]
        if "name" not in columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN name TEXT")

        findings_columns = [row["name"] for row in conn.execute("PRAGMA table_info(findings)").fetchall()]
        if "task_id" not in findings_columns:
            conn.execute("ALTER TABLE findings ADD COLUMN task_id TEXT")
        if "tool_run_id" not in findings_columns:
            conn.execute("ALTER TABLE findings ADD COLUMN tool_run_id INTEGER")

        conn.commit()

        chat_columns = [row["name"] for row in conn.execute("PRAGMA table_info(chat_messages)").fetchall()]
        if "metadata" not in chat_columns:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN metadata TEXT")


def save_session(session_id: str, name: str | None, created_at: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (session_id, name, created_at, status)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, name, created_at, status),
        )
        conn.commit()


def save_task(task) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tasks
            (id, session_id, objective, target, category, approved, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.session_id,
                task.objective,
                task.target,
                task.category,
                int(task.approved),
                task.created_at.isoformat(),
            ),
        )
        conn.commit()


def list_sessions(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                s.session_id,
                s.name,
                s.created_at,
                s.status,
                COUNT(DISTINCT f.id) AS finding_count,
                COUNT(DISTINCT tr.id) AS tool_run_count,
                CASE WHEN COUNT(DISTINCT sm.id) > 0 THEN 1 ELSE 0 END AS has_memory
            FROM sessions s
            LEFT JOIN findings f ON s.session_id = f.session_id
            LEFT JOIN tool_runs tr ON s.session_id = tr.session_id
            LEFT JOIN session_memory sm ON s.session_id = sm.session_id
            GROUP BY s.session_id, s.name, s.created_at, s.status
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def get_session_by_name(name: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id, name, created_at, status
            FROM sessions
            WHERE lower(name) = lower(?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (name,),
        ).fetchone()

    return dict(row) if row else None


def get_session_by_id(session_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id, name, created_at, status
            FROM sessions
            WHERE session_id = ?
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    return dict(row) if row else None


def get_latest_session_id() -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id
            FROM sessions
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

    return row["session_id"] if row else None


def save_tool_run(
    session_id: str,
    tool_name: str,
    command_preview: str,
    stdout_path: str | None,
    stderr_path: str | None,
    returncode: int,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tool_runs
            (session_id, tool_name, command_preview, stdout_path, stderr_path, returncode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                tool_name,
                command_preview,
                stdout_path,
                stderr_path,
                returncode,
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def save_findings(
    session_id: str,
    parsed_output: dict,
    task_id: str | None = None,
    tool_run_id: int | None = None,
) -> None:
    host = parsed_output.get("host")
    os_hint = parsed_output.get("os_hint")

    with get_connection() as conn:
        for item in parsed_output.get("port_details", []):
            conn.execute(
                """
                INSERT INTO findings
                (session_id, task_id, tool_run_id, host, port, protocol, state, service, version, os_hint, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    task_id,
                    tool_run_id,
                    host,
                    item.get("port"),
                    item.get("protocol"),
                    item.get("state"),
                    item.get("service"),
                    item.get("version"),
                    os_hint,
                    datetime.now(UTC).isoformat(),
                ),
            )
        conn.commit()


def get_findings_by_session(session_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT task_id, tool_run_id, host, port, protocol, state, service, version, os_hint, created_at
            FROM findings
            WHERE session_id = ?
            ORDER BY port ASC
            """,
            (session_id,),
        ).fetchall()

    return [dict(row) for row in rows]

def get_tool_runs_by_session(session_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, session_id, tool_name, command_preview, stdout_path, stderr_path, returncode, created_at
            FROM tool_runs
            WHERE session_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (session_id,),
        ).fetchall()

    return [dict(row) for row in rows]

def get_tool_run_by_id(tool_run_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, session_id, tool_name, command_preview, stdout_path, stderr_path, returncode, created_at
            FROM tool_runs
            WHERE id = ?
            LIMIT 1
            """,
            (tool_run_id,),
        ).fetchone()

    return dict(row) if row else None

def get_task_by_id(task_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, session_id, objective, target, category, approved, created_at
            FROM tasks
            WHERE id = ?
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()

    return dict(row) if row else None


def _encode_list(value: list[str] | None) -> str:
    return json.dumps(value or [])


def _decode_list(value: str | None) -> list[str]:
    if not value:
        return []

    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []

    if not isinstance(decoded, list):
        return []

    return [str(item) for item in decoded]

def _encode_dict(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {})


def _decode_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}

    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}

    if not isinstance(decoded, dict):
        return {}

    return decoded

def save_session_memory(session_id: str, data: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO session_memory
            (session_id, summary, observations, unresolved, suggestions, tags, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                str(data.get("summary") or ""),
                _encode_list(data.get("observations")),
                _encode_list(data.get("unresolved")),
                _encode_list(data.get("suggestions")),
                _encode_list(data.get("tags")),
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()


def get_session_memory(session_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id, summary, observations, unresolved, suggestions, tags, updated_at
            FROM session_memory
            WHERE session_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    if not row:
        return None

    return {
        "session_id": row["session_id"],
        "summary": row["summary"],
        "observations": _decode_list(row["observations"]),
        "unresolved": _decode_list(row["unresolved"]),
        "suggestions": _decode_list(row["suggestions"]),
        "tags": _decode_list(row["tags"]),
        "updated_at": row["updated_at"],
    }
    
def save_chat_message(
    session_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (session_id, role, content, metadata, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                _encode_dict(metadata),
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()


def get_chat_messages(session_id: str, limit: int = 20) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, session_id, role, content, metadata, created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()

    messages = [
        {
            **dict(row),
            "metadata": _decode_dict(row["metadata"]),
        }
        for row in rows
    ]
    messages.reverse()
    return messages


def save_session_state(session_id: str, data: dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO session_state (
                session_id,
                current_target,
                current_objective,
                active_hypotheses,
                unresolved_items,
                tool_state,
                next_steps,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                current_target = excluded.current_target,
                current_objective = excluded.current_objective,
                active_hypotheses = excluded.active_hypotheses,
                unresolved_items = excluded.unresolved_items,
                tool_state = excluded.tool_state,
                next_steps = excluded.next_steps,
                updated_at = excluded.updated_at
            """,
            (
                session_id,
                data.get("current_target"),
                data.get("current_objective"),
                _encode_list(data.get("active_hypotheses")),
                _encode_list(data.get("unresolved_items")),
                _encode_dict(data.get("tool_state")),
                _encode_list(data.get("next_steps")),
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()


def get_session_state(session_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                session_id,
                current_target,
                current_objective,
                active_hypotheses,
                unresolved_items,
                tool_state,
                next_steps,
                updated_at
            FROM session_state
            WHERE session_id = ?
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    if not row:
        return None

    return {
        "session_id": row["session_id"],
        "current_target": row["current_target"],
        "current_objective": row["current_objective"],
        "active_hypotheses": _decode_list(row["active_hypotheses"]),
        "unresolved_items": _decode_list(row["unresolved_items"]),
        "tool_state": _decode_dict(row["tool_state"]),
        "next_steps": _decode_list(row["next_steps"]),
        "updated_at": row["updated_at"],
    }


def save_long_term_memory(
    memory_type: str,
    content: str,
    tags: list[str] | None = None,
    memory_key: str | None = None,
    source_session_id: str | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO long_term_memories (
                memory_type,
                memory_key,
                content,
                tags,
                source_session_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_type,
                memory_key,
                content,
                _encode_list(tags),
                source_session_id,
                datetime.now(UTC).isoformat(),
                datetime.now(UTC).isoformat(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_long_term_memories(limit: int = 50, memory_type: str | None = None) -> list[dict]:
    with get_connection() as conn:
        if memory_type:
            rows = conn.execute(
                """
                SELECT
                    id,
                    memory_type,
                    memory_key,
                    content,
                    tags,
                    source_session_id,
                    created_at,
                    updated_at
                FROM long_term_memories
                WHERE memory_type = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (memory_type, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    id,
                    memory_type,
                    memory_key,
                    content,
                    tags,
                    source_session_id,
                    created_at,
                    updated_at
                FROM long_term_memories
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [
        {
            "id": row["id"],
            "memory_type": row["memory_type"],
            "memory_key": row["memory_key"],
            "content": row["content"],
            "tags": _decode_list(row["tags"]),
            "source_session_id": row["source_session_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]


def search_long_term_memories(
    query: str,
    limit: int = 10,
    memory_type: str | None = None,
) -> list[dict]:
    like_query = f"%{query.strip()}%"

    with get_connection() as conn:
        if memory_type:
            rows = conn.execute(
                """
                SELECT
                    id,
                    memory_type,
                    memory_key,
                    content,
                    tags,
                    source_session_id,
                    created_at,
                    updated_at
                FROM long_term_memories
                WHERE memory_type = ?
                  AND (
                    content LIKE ?
                    OR tags LIKE ?
                    OR COALESCE(memory_key, '') LIKE ?
                  )
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (memory_type, like_query, like_query, like_query, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT
                    id,
                    memory_type,
                    memory_key,
                    content,
                    tags,
                    source_session_id,
                    created_at,
                    updated_at
                FROM long_term_memories
                WHERE
                    content LIKE ?
                    OR tags LIKE ?
                    OR COALESCE(memory_key, '') LIKE ?
                    OR memory_type LIKE ?
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (like_query, like_query, like_query, like_query, limit),
            ).fetchall()

    return [
        {
            "id": row["id"],
            "memory_type": row["memory_type"],
            "memory_key": row["memory_key"],
            "content": row["content"],
            "tags": _decode_list(row["tags"]),
            "source_session_id": row["source_session_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]

