import sqlite3
from datetime import datetime
from pathlib import Path

from app.storage.models import (
    CREATE_SESSIONS_TABLE,
    CREATE_TASKS_TABLE,
    CREATE_TOOL_RUNS_TABLE,
    CREATE_FINDINGS_TABLE,
)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "spectremind.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(CREATE_SESSIONS_TABLE)
        conn.execute(CREATE_TASKS_TABLE)
        conn.execute(CREATE_TOOL_RUNS_TABLE)
        conn.execute(CREATE_FINDINGS_TABLE)

        columns = [row["name"] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()]
        if "name" not in columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN name TEXT")

        conn.commit()


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
                COUNT(f.id) AS finding_count
            FROM sessions s
            LEFT JOIN findings f ON s.session_id = f.session_id
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

def save_tool_run(
    session_id: str,
    tool_name: str,
    command_preview: str,
    stdout_path: str | None,
    stderr_path: str | None,
    returncode: int,
) -> None:
    with get_connection() as conn:
        conn.execute(
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
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def save_findings(session_id: str, parsed_output: dict) -> None:
    host = parsed_output.get("host")
    os_hint = parsed_output.get("os_hint")

    with get_connection() as conn:
        for item in parsed_output.get("port_details", []):
            conn.execute(
                """
                INSERT INTO findings
                (session_id, host, port, protocol, state, service, version, os_hint, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    host,
                    item.get("port"),
                    item.get("protocol"),
                    item.get("state"),
                    item.get("service"),
                    item.get("version"),
                    os_hint,
                    datetime.utcnow().isoformat(),
                ),
            )
        conn.commit()




def get_findings_by_session(session_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT host, port, protocol, state, service, version, os_hint, created_at
            FROM findings
            WHERE session_id = ?
            ORDER BY port ASC
            """,
            (session_id,),
        ).fetchall()

    return [dict(row) for row in rows]


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