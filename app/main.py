
from __future__ import annotations

from pathlib import Path

import typer
from rich import print

from app.core.intent_parser import parse_intent
from app.core.orchestrator import Orchestrator
from app.core.session import create_session, get_session_path
from app.core.session_memory import get_session_memory
from app.core.spectremind_core import SpectreMindCore
from app.reports.markdown import save_markdown_report
from app.schemas.tasks import Task
from app.storage.db import (
    get_findings_by_session,
    get_latest_session_id,
    get_session_by_id,
    get_session_by_name,
    get_task_by_id,
    get_tool_run_by_id,
    get_tool_runs_by_session,
    init_db,
    list_sessions,
)

core = SpectreMindCore()

cli = typer.Typer(help="SpectreMind CLI")
init_db()

def session_artifact_flags(session_id: str) -> dict[str, bool]:
    session_path = get_session_path(session_id)
    return {
        "report": (session_path / "report.md").exists(),
        "stdout": (session_path / "nmap_stdout.txt").exists(),
        "stderr": (session_path / "nmap_stderr.txt").exists(),
        "events": (session_path / "events.jsonl").exists(),
    }


def build_flag_text(flags: list[str]) -> str:
    return ", ".join(flags) if flags else "none"

def pretty_print(result: dict) -> None:
    print(f"[bold cyan]Agent:[/bold cyan] {result['agent']}")
    print(f"[bold green]Status:[/bold green] {result['status']}")
    print(f"[bold yellow]Summary:[/bold yellow] {result['summary']}")

    data = result.get("data", {})
    watcher = data.get("watcher_result") or {}
    resolved_session_id = data.get("session_id")
    memories = data.get("memories") or []
    if memories:
        print("\n[cyan]Memories:[/cyan]")
        for item in memories:
            tag_text = f" | Tags: {', '.join(item.get('tags', []))}" if item.get("tags") else ""
            key_text = f" | Key: {item['memory_key']}" if item.get("memory_key") else ""
            print(f"- ID: {item['id']} | Type: {item['memory_type']}{key_text}{tag_text}")
            print(f"  {item['content']}")

    if resolved_session_id:
        print(f"[bold white]Session:[/bold white] {resolved_session_id}")

    tool_card = data.get("tool_card") or {}
    if tool_card:
        print(
            f"[bold blue]Tool:[/bold blue] "
            f"{tool_card['display_name']} ({tool_card['key']}) "
            f"| Approval: {tool_card['approval_class']}"
        )

    if watcher.get("summary"):
        print(f"[bold magenta]Watcher:[/bold magenta] {watcher['summary']}")

    if watcher.get("priority") == "high" and watcher.get("unresolved"):
        print("\n[magenta]Unresolved:[/magenta]")
        for item in watcher["unresolved"]:
            print(f"- {item}")

    if result.get("next_steps"):
        print("\n[cyan]Next Steps:[/cyan]")
        for step in result["next_steps"]:
            print(f"- {step}")


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
    session_name: str = typer.Option("", help="Name for a new or existing session"),
):
    if not session_id:
        if session_name:
            existing = get_session_by_name(session_name)
            if existing:
                session_id = existing["session_id"]
            else:
                session = create_session(name=session_name or None)
                session_id = session["session_id"]
        else:
            session = create_session(name=None)
            session_id = session["session_id"]

    task = Task(
        session_id=session_id,
        objective=objective,
        target=target or None,
        approved=approved,
    )

    orchestrator = Orchestrator()
    result = orchestrator.run_task(task)

    print(
        {
            "status": result["status"],
            "session_id": session_id,
            "plan": result.get("plan"),
            "next_steps": result.get("next_steps", []),
        }
    )

    watcher = result.get("watcher_result") or {}
    if watcher.get("summary"):
        print(f"[magenta]Watcher:[/magenta] {watcher['summary']}")

    if result.get("report"):
        report_path = get_session_path(session_id) / "report.md"
        print(f"[cyan]Report saved to:[/cyan] {report_path}")


@cli.command()
def sessions(
    limit: int = typer.Option(10, help="Number of recent sessions to show"),
):
    rows = list_sessions(limit=limit)
    latest_session_id = get_latest_session_id()

    if not rows:
        print("[yellow]No sessions found.[/yellow]")
        raise typer.Exit(code=0)

    print("[green]Recent sessions:[/green]")

    for row in rows:
        session_id = row["session_id"]
        artifact_flags = session_artifact_flags(session_id)

        markers: list[str] = []
        if session_id == latest_session_id:
            markers.append("latest")
        if row.get("has_memory"):
            markers.append("memory")
        if artifact_flags["report"]:
            markers.append("report")
        if artifact_flags["stdout"]:
            markers.append("stdout")
        if artifact_flags["stderr"]:
            markers.append("stderr")
        if artifact_flags["events"]:
            markers.append("events")

        name_text = f" | Name: {row['name']}" if row.get("name") else ""
        marker_text = f" | Flags: {build_flag_text(markers)}"

        print(
            f"- ID: {session_id}"
            f"{name_text}"
            f" | Created: {row['created_at']}"
            f" | Status: {row['status']}"
            f" | Findings: {row['finding_count']}"
            f" | Tool Runs: {row.get('tool_run_count', 0)}"
            f"{marker_text}"
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
    memory = get_session_memory(resolved)

    print(f"[green]Session:[/green] {row['session_id']}")
    print(f"Name: {row.get('name') or 'None'}")
    print(f"Created: {row['created_at']}")
    print(f"Status: {row['status']}")
    print(f"Path: {session_path}")
    print(f"Report: {report_path if report_path.exists() else 'Missing'}")
    print(f"Stdout: {stdout_path if stdout_path.exists() else 'Missing'}")
    print(f"Stderr: {stderr_path if stderr_path.exists() else 'Missing'}")
    print(f"Events: {events_path if events_path.exists() else 'Missing'}")

    if memory:
        print("\n[magenta]Session Memory:[/magenta]")
        print(f"Summary: {memory['summary']}")
        print(f"Updated: {memory['updated_at']}")

        if memory.get("tags"):
            print(f"Tags: {', '.join(memory['tags'])}")

        if memory.get("unresolved"):
            print("Unresolved:")
            for item in memory["unresolved"]:
                print(f"- {item}")


@cli.command(name="session-memory")
def session_memory_show(
    session_id: str = typer.Option("", help="Session ID to inspect"),
    session_name: str = typer.Option("", help="Named session to inspect"),
    latest: bool = typer.Option(False, help="Use latest session"),
):
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)

    if not resolved:
        print("[red]Could not resolve session for memory lookup.[/red]")
        raise typer.Exit(code=1)

    memory = get_session_memory(resolved)
    if not memory:
        print("[yellow]No session memory found.[/yellow]")
        raise typer.Exit(code=0)

    print(f"[green]Session memory for:[/green] {resolved}")
    print(f"Updated: {memory['updated_at']}")
    print(f"Summary: {memory['summary']}")

    if memory.get("observations"):
        print("\n[cyan]Observations:[/cyan]")
        for item in memory["observations"]:
            print(f"- {item}")

    if memory.get("unresolved"):
        print("\n[yellow]Unresolved:[/yellow]")
        for item in memory["unresolved"]:
            print(f"- {item}")

    if memory.get("suggestions"):
        print("\n[green]Suggestions:[/green]")
        for item in memory["suggestions"]:
            print(f"- {item}")

    if memory.get("tags"):
        print(f"\n[magenta]Tags:[/magenta] {', '.join(memory['tags'])}")


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
        task_text = f" | Task: {row['task_id']}" if row.get("task_id") else ""
        run_text = f" | Tool Run: {row['tool_run_id']}" if row.get("tool_run_id") else ""

        print(
            f"- {row['port']}/{row['protocol']} | "
            f"State: {row['state']} | "
            f"Service: {row['service']}{version}{os_hint}"
            f"{task_text}{run_text}"
        )

@cli.command(name="tool-runs")
def tool_runs(
    session_id: str = typer.Option("", help="Session ID to inspect"),
    session_name: str = typer.Option("", help="Named session to inspect"),
    latest: bool = typer.Option(False, help="Use latest session"),
):
    resolved = resolve_session_id(session_id=session_id, session_name=session_name, latest=latest)

    if not resolved:
        print("[red]Could not resolve session for tool-run lookup.[/red]")
        raise typer.Exit(code=1)

    rows = get_tool_runs_by_session(resolved)

    if not rows:
        print(f"[yellow]No tool runs found for session:[/yellow] {resolved}")
        raise typer.Exit(code=0)

    print(f"[green]Tool runs for session:[/green] {resolved}")

    for row in rows:
        stdout_text = f" | Stdout: {row['stdout_path']}" if row.get("stdout_path") else ""
        stderr_text = f" | Stderr: {row['stderr_path']}" if row.get("stderr_path") else ""
        print(
            f"- Run ID: {row['id']} | "
            f"Tool: {row['tool_name']} | "
            f"Return Code: {row['returncode']} | "
            f"Created: {row['created_at']} | "
            f"Command: {row['command_preview']}"
            f"{stdout_text}{stderr_text}"
        )

@cli.command(name="tool-run-show")
def tool_run_show(
    run_id: int = typer.Option(..., help="Tool run ID to inspect"),
):
    row = get_tool_run_by_id(run_id)

    if not row:
        print("[red]Tool run not found.[/red]")
        raise typer.Exit(code=1)

    print(f"[green]Tool run:[/green] {row['id']}")
    print(f"Session: {row['session_id']}")
    print(f"Tool: {row['tool_name']}")
    print(f"Created: {row['created_at']}")
    print(f"Return Code: {row['returncode']}")
    print(f"Command: {row['command_preview']}")
    print(f"Stdout: {row['stdout_path'] or 'Missing'}")
    print(f"Stderr: {row['stderr_path'] or 'Missing'}")

@cli.command(name="task-show")
def task_show(
    task_id: str = typer.Option(..., help="Task ID to inspect"),
):
    row = get_task_by_id(task_id)

    if not row:
        print("[red]Task not found.[/red]")
        raise typer.Exit(code=1)

    print(f"[green]Task:[/green] {row['id']}")
    print(f"Session: {row['session_id']}")
    print(f"Objective: {row['objective']}")
    print(f"Target: {row['target'] or 'None'}")
    print(f"Category: {row['category']}")
    print(f"Approved: {bool(row['approved'])}")
    print(f"Created: {row['created_at']}")

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
    session_id: str = typer.Option("", help="Reuse an existing session ID"),
    session_name: str = typer.Option("", help="Reuse or create a named session"),
    latest: bool = typer.Option(False, help="Reuse the latest session"),
):
    result = core.handle(
        text=text,
        approved=approved,
        session_id=session_id,
        session_name=session_name,
        latest=latest,
    )
    pretty_print(result)


if __name__ == "__main__":
    cli()