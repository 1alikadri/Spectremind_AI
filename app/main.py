from pathlib import Path

import typer
from rich import print

from app.storage.db import (
    init_db,
    get_findings_by_session,
    get_latest_session_id,
    list_sessions,
    get_session_by_name,
    get_session_by_id,
)
from app.core.intent_parser import parse_intent
from app.core.session import create_session, get_session_path
from app.schemas.tasks import Task
from app.core.orchestrator import Orchestrator
from app.reports.markdown import save_markdown_report

cli = typer.Typer(help="SpectreMind CLI")
init_db()


def resolve_session_id(session_id: str = "", session_name: str = "", latest: bool = False) -> str:
    if latest:
        return get_latest_session_id() or ""

    if session_id:
        return session_id

    if session_name:
        match = get_session_by_name(session_name)
        return match["session_id"] if match else ""

    return ""


@cli.command()
def init(
    name: str = typer.Option("", help="Optional human-readable session name"),
):
    session = create_session(name=name or None)
    display_name = f" ({session['name']})" if session.get("name") else ""
    print(f"[green]Session created:[/green] {session['session_id']}{display_name}")


@cli.command()
def run(
    objective: str = typer.Option(..., help="Task objective"),
    target: str = typer.Option("", help="Target host/IP"),
    approved: bool = typer.Option(False, help="Explicitly approve tool execution"),
    session_id: str = typer.Option("", help="Existing session ID"),
    session_name: str = typer.Option("", help="Name for a new session"),
):
    if not session_id:
        session = create_session(name=session_name or None)
        session_id = session["session_id"]

    task = Task(
        session_id=session_id,
        objective=objective,
        target=target or None,
        approved=approved,
    )

    orchestrator = Orchestrator()
    result = orchestrator.run_task(task)

    print({
        "status": result["status"],
        "plan": result["plan"],
        "next_steps": result.get("next_steps"),
    })

    if result.get("report"):
        report_path = get_session_path(session_id) / "report.md"
        save_markdown_report(report_path, result["report"])
        print(f"[cyan]Report saved to:[/cyan] {report_path}")


@cli.command()
def sessions(
    limit: int = typer.Option(10, help="Number of recent sessions to show"),
):
    rows = list_sessions(limit=limit)

    if not rows:
        print("[yellow]No sessions found.[/yellow]")
        raise typer.Exit(code=0)

    print("[green]Recent sessions:[/green]")

    for row in rows:
        name_text = f" | Name: {row['name']}" if row.get("name") else ""
        print(
            f"- ID: {row['session_id']}"
            f"{name_text}"
            f" | Created: {row['created_at']}"
            f" | Status: {row['status']}"
            f" | Findings: {row['finding_count']}"
        )


@cli.command(name="session-show")
def session_show(
    session_id: str = typer.Option("", help="Session ID to inspect"),
    session_name: str = typer.Option("", help="Named session to inspect"),
    latest: bool = typer.Option(False, help="Use latest session"),
):
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)

    if not resolved:
        print("[red]Could not resolve session.[/red]")
        raise typer.Exit(code=1)

    row = get_session_by_id(resolved)

    if not row:
        print("[red]Session not found.[/red]")
        raise typer.Exit(code=1)

    session_path = get_session_path(resolved)
    report_path = session_path / "report.md"
    stdout_path = session_path / "nmap_stdout.txt"
    stderr_path = session_path / "nmap_stderr.txt"
    events_path = session_path / "events.jsonl"

    print(f"[green]Session:[/green] {row['session_id']}")
    print(f"Name: {row.get('name') or 'None'}")
    print(f"Created: {row['created_at']}")
    print(f"Status: {row['status']}")
    print(f"Path: {session_path}")
    print(f"Report: {report_path if report_path.exists() else 'Missing'}")
    print(f"Stdout: {stdout_path if stdout_path.exists() else 'Missing'}")
    print(f"Stderr: {stderr_path if stderr_path.exists() else 'Missing'}")
    print(f"Events: {events_path if events_path.exists() else 'Missing'}")


@cli.command()
def findings(
    session_id: str = typer.Option("", help="Session ID to inspect"),
    session_name: str = typer.Option("", help="Named session to inspect"),
    latest: bool = typer.Option(False, help="Use latest session"),
):
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)

    if not resolved:
        print("[red]No session selector provided and no latest session found.[/red]")
        raise typer.Exit(code=1)

    rows = get_findings_by_session(resolved)

    if not rows:
        print(f"[yellow]No open-port findings found for session:[/yellow] {resolved}")
        print("[cyan]Check the session report and raw Nmap output for filtered or closed port evidence.[/cyan]")
        raise typer.Exit(code=0)

    print(f"[green]Findings for session:[/green] {resolved}")

    for row in rows:
        version = f" | Version: {row['version']}" if row["version"] else ""
        os_hint = f" | OS Hint: {row['os_hint']}" if row["os_hint"] else ""
        print(
            f"- {row['port']}/{row['protocol']} | "
            f"State: {row['state']} | "
            f"Service: {row['service']}{version}{os_hint}"
        )


@cli.command()
def report(
    session_id: str = typer.Option("", help="Session ID to inspect"),
    session_name: str = typer.Option("", help="Named session to inspect"),
    latest: bool = typer.Option(False, help="Use latest session"),
):
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)

    if not resolved:
        print("[red]Could not resolve session for report lookup.[/red]")
        raise typer.Exit(code=1)

    report_path = get_session_path(resolved) / "report.md"

    if not report_path.exists():
        print("[yellow]Report not found for session.[/yellow]")
        raise typer.Exit(code=0)

    print(f"[green]Report path:[/green] {report_path}")
    print(report_path.read_text(encoding="utf-8"))


@cli.command()
def artifacts(
    session_id: str = typer.Option("", help="Session ID to inspect"),
    session_name: str = typer.Option("", help="Named session to inspect"),
    latest: bool = typer.Option(False, help="Use latest session"),
):
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)

    if not resolved:
        print("[red]Could not resolve session for artifact lookup.[/red]")
        raise typer.Exit(code=1)

    session_path = get_session_path(resolved)

    artifact_paths = {
        "session": session_path,
        "report": session_path / "report.md",
        "stdout": session_path / "nmap_stdout.txt",
        "stderr": session_path / "nmap_stderr.txt",
        "events": session_path / "events.jsonl",
    }

    print(f"[green]Artifacts for session:[/green] {resolved}")
    for label, path in artifact_paths.items():
        status = str(path) if path.exists() else "Missing"
        print(f"- {label}: {status}")


@cli.command()
def ask(
    text: str = typer.Option(..., help="Natural language request"),
    approved: bool = typer.Option(False, help="Explicitly approve tool execution"),
):
    intent = parse_intent(text)

    print({
        "intent": intent.action,
        "reason": intent.reason,
    })

    if intent.action == "blocked":
        print("[red]Request blocked.[/red]")
        raise typer.Exit(code=1)

    if intent.action == "create_session":
        session = create_session(name=intent.session_name)
        print({
            "session_id": session["session_id"],
            "name": session.get("name"),
            "status": session["status"],
        })
        return

    if intent.action == "list_sessions":
        rows = list_sessions(limit=10)

        if not rows:
            print("[yellow]No sessions found.[/yellow]")
            raise typer.Exit(code=0)

        print("[green]Recent sessions:[/green]")
        for row in rows:
            name_text = f" | Name: {row['name']}" if row.get("name") else ""
            print(
                f"- ID: {row['session_id']}"
                f"{name_text}"
                f" | Created: {row['created_at']}"
                f" | Status: {row['status']}"
                f" | Findings: {row['finding_count']}"
            )
        return

    if intent.action == "show_findings":
        resolved = resolve_session_id(session_name=intent.session_name or "", latest=intent.use_latest)

        if not resolved:
            print("[red]Could not resolve a session for findings lookup.[/red]")
            raise typer.Exit(code=1)

        rows = get_findings_by_session(resolved)

        if not rows:
            print(f"[yellow]No open-port findings found for session:[/yellow] {resolved}")
            print("[cyan]Check the session report and raw Nmap output for filtered or closed port evidence.[/cyan]")
            raise typer.Exit(code=0)

        print(f"[green]Findings for session:[/green] {resolved}")
        for row in rows:
            version = f" | Version: {row['version']}" if row["version"] else ""
            print(
                f"- {row['port']}/{row['protocol']} | "
                f"State: {row['state']} | Service: {row['service']}{version}"
            )
        return

    if intent.action == "show_session":
        resolved = resolve_session_id(session_name=intent.session_name or "", latest=intent.use_latest)

        if not resolved:
            print("[red]Could not resolve a session.[/red]")
            raise typer.Exit(code=1)

        row = get_session_by_id(resolved)
        if not row:
            print("[red]Session not found.[/red]")
            raise typer.Exit(code=1)

        print(row)
        return

    if intent.action == "show_report":
        resolved = resolve_session_id(session_name=intent.session_name or "", latest=intent.use_latest)

        if not resolved:
            print("[red]Could not resolve a session for report lookup.[/red]")
            raise typer.Exit(code=1)

        report_path = get_session_path(resolved) / "report.md"
        if not report_path.exists():
            print("[yellow]Report not found for session.[/yellow]")
            raise typer.Exit(code=0)

        print(report_path.read_text(encoding="utf-8"))
        return

    if intent.action == "show_artifacts":
        resolved = resolve_session_id(session_name=intent.session_name or "", latest=intent.use_latest)

        if not resolved:
            print("[red]Could not resolve a session for artifact lookup.[/red]")
            raise typer.Exit(code=1)

        session_path = get_session_path(resolved)
        print({
            "session": str(session_path),
            "report": str(session_path / "report.md"),
            "stdout": str(session_path / "nmap_stdout.txt"),
            "stderr": str(session_path / "nmap_stderr.txt"),
            "events": str(session_path / "events.jsonl"),
        })
        return

    if intent.action == "run_scan":
        task_session = create_session(name=intent.session_name or None)

        task = Task(
            session_id=task_session["session_id"],
            objective=intent.objective or "Natural language scan request",
            target=intent.target,
            approved=approved,
        )

        orchestrator = Orchestrator()
        result = orchestrator.run_task(task)

        print({
            "status": result["status"],
            "plan": result["plan"],
            "next_steps": result.get("next_steps"),
        })

        if result.get("report"):
            report_path = get_session_path(task_session["session_id"]) / "report.md"
            save_markdown_report(report_path, result["report"])
            print(f"[cyan]Report saved to:[/cyan] {report_path}")
        return

    print("[yellow]Request not understood or not supported yet.[/yellow]")


if __name__ == "__main__":
    cli()