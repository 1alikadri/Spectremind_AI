from __future__ import annotations

from app.schemas.tasks import Task
from app.storage import db


def _init_temp_db(monkeypatch, tmp_path):
    temp_db_path = tmp_path / "spectremind_execution_readers_test.db"
    monkeypatch.setattr(db, "DB_PATH", temp_db_path)
    db.init_db()
    return temp_db_path


def _create_session(session_id: str, name: str | None = None) -> None:
    db.save_session(
        session_id=session_id,
        name=name,
        created_at="2026-04-10T00:00:00+00:00",
        status="active",
    )


def test_get_tool_run_by_id_returns_saved_run(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    _create_session("session-1", "alpha")

    run_id = db.save_tool_run(
        session_id="session-1",
        tool_name="nmap",
        command_preview="nmap -Pn -sV test.local",
        stdout_path="stdout.txt",
        stderr_path="stderr.txt",
        returncode=0,
    )

    row = db.get_tool_run_by_id(run_id)

    assert row is not None
    assert row["id"] == run_id
    assert row["tool_name"] == "nmap"


def test_get_task_by_id_returns_saved_task(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    _create_session("session-2", "beta")

    task = Task(
        session_id="session-2",
        objective="scan beta.local",
        target="beta.local",
        approved=True,
    )
    db.save_task(task)

    row = db.get_task_by_id(task.id)

    assert row is not None
    assert row["id"] == task.id
    assert row["objective"] == "scan beta.local"