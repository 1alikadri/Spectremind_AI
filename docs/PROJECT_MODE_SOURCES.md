# SpectreMind Project Mode Sources

Use these files as ChatGPT Project sources for SpectreMind. This set gives enough context for architecture, behavior, storage, tools, and intended agent roles without overwhelming the project.

## Core architecture

- `app/core/spectremind_core.py` — Main system entrypoint that keeps SpectreMind as the single external voice and routes requests.
- `app/core/orchestrator.py` — Controls operational flow from planning to scope validation, tool execution, parsing, WATCHER processing, storage, and reporting.
- `app/core/intent_parser.py` — Parses natural-language requests into structured intents for routing.
- `app/core/session.py` — Creates and locates sessions for persistent, operator-controlled workflows.
- `app/core/session_memory.py` — Thin interface for saving and loading WATCHER session-memory snapshots.
- `app/core/scope.py` — Enforces single-target validation and blocks unsafe target formats before execution.
- `app/core/logger.py` — Writes timestamped event logs for session traceability.
- `app/core/files.py` — Saves raw tool artifacts like stdout and stderr into the session directory.
- `app/core/llm_client.py` — Local LLM client used by internal agents while keeping execution local-first.

## Agents

- `app/agents/aether.py` — Planning/orchestration agent that classifies tasks and decides the execution action.
- `app/agents/watcher.py` — Session intelligence agent that observes parsed results, maintains memory, and produces rule-based suggestions.
- `app/agents/scribe.py` — Reporting agent that converts structured findings into operator-facing summaries and markdown reports.

## Parser and reports

- `app/parsers/nmap_parser.py` — Converts raw Nmap output into structured data used by storage, WATCHER, and reporting.
- `app/reports/markdown.py` — Saves the final markdown report to disk.

## Storage and schemas

- `app/storage/db.py` — SQLite access layer for sessions, findings, tool runs, and session-memory snapshots.
- `app/storage/models.py` — SQL schema definitions for database initialization.
- `app/schemas/intents.py` — Intent data model used by the parser and SpectreMindCore.
- `app/schemas/tasks.py` — Task model used for orchestrator execution.
- `app/schemas/responses.py` — Structured response contracts for WATCHER, orchestration, and SpectreMind output.

## Tools

- `app/tools/registry.py` — Tool registry that exposes which tools the orchestrator may call.
- `app/tools/base.py` — Base interface for all tools.
- `app/tools/wrappers/nmap_wrapper.py` — Local Nmap wrapper used for approved scanning.

## App entry and config

- `app/main.py` — CLI entrypoint that exposes init, run, ask, findings, report, artifacts, and session views.
- `app/config.py` — Defines local directories and LLM configuration.

## Recommended tests

- `app/tests/test_watcher.py` — Verifies WATCHER trigger rules, parser behavior, and merged session-memory behavior.
- `app/tests/test_db_session_memory.py` — Verifies session-memory persistence and retrieval behavior.
- `app/tests/test_memory_service.py` — Verifies chat message, session state, and long-term memory round trips.
- `app/tests/test_orchestrator.py` — Verifies approval gating, scope blocking, artifact/report persistence, and tool errors.
- `app/tests/test_spectremind_memory_integration.py` — Verifies chat persistence, session-state persistence, and memory save/recall routing through SpectreMindCore.
- `app/tests/test_intent_parser.py` — Verifies hard-blocking, rule parsing, router fallback, and fail-closed behavior.
- `app/tests/test_intent_router.py` — Verifies bounded LLM-assisted routing constraints.
- `app/tests/test_tool_registry.py` — Verifies structured tool metadata registration.