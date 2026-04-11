from __future__ import annotations
from app.schemas.tasks import Task
from app.storage import db


def _init_temp_db(monkeypatch, tmp_path):
    temp_db_path = tmp_path / "spectremind_findings_test.db"
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


def test_save_findings_preserves_task_and_tool_run_provenance(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    session_id = "session-findings"
    _create_session(session_id, name="alpha")

    parsed_output = {
        "host": "test.local",
        "os_hint": "Linux",
        "port_details": [
            {
                "port": 80,
                "protocol": "tcp",
                "state": "open",
                "service": "http",
                "version": "nginx 1.24.0",
            }
        ],
    }

    task = Task(
        session_id=session_id,
        objective="scan test.local",
        target="test.local",
        approved=True,
    )
    db.save_task(task)

    tool_run_id = db.save_tool_run(
        session_id=session_id,
        tool_name="nmap",
        command_preview="nmap -Pn -sV test.local",
        stdout_path="stdout.txt",
        stderr_path="stderr.txt",
        returncode=0,
    )

    db.save_findings(
        session_id=session_id,
        parsed_output=parsed_output,
        task_id=task.id,
        tool_run_id=tool_run_id,
    )
    rows = db.get_findings_by_session(session_id)

    assert len(rows) == 1
    assert rows[0]["task_id"] == task.id
    assert rows[0]["tool_run_id"] == tool_run_id
    assert rows[0]["host"] == "test.local"
    assert rows[0]["port"] == 80
    assert rows[0]["service"] == "http"