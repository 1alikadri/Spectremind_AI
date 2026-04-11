from __future__ import annotations

from app.storage import db


def _init_temp_db(monkeypatch, tmp_path):
    temp_db_path = tmp_path / "spectremind_tool_runs_test.db"
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


def test_get_tool_runs_by_session_returns_runs_in_reverse_chronological_order(monkeypatch, tmp_path):
    _init_temp_db(monkeypatch, tmp_path)
    session_id = "session-runs"
    _create_session(session_id, name="alpha")

    first_id = db.save_tool_run(
        session_id=session_id,
        tool_name="nmap",
        command_preview="nmap -Pn -sV one.local",
        stdout_path="one_stdout.txt",
        stderr_path="one_stderr.txt",
        returncode=0,
    )
    second_id = db.save_tool_run(
        session_id=session_id,
        tool_name="http_probe",
        command_preview="http_probe one.local",
        stdout_path="two_stdout.txt",
        stderr_path="two_stderr.txt",
        returncode=0,
    )

    rows = db.get_tool_runs_by_session(session_id)

    assert len(rows) == 2
    assert rows[0]["id"] == second_id
    assert rows[1]["id"] == first_id
    assert rows[0]["tool_name"] == "http_probe"
    assert rows[1]["tool_name"] == "nmap"