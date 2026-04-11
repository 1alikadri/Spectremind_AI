# SpectreMind Project File Map

This file explains the current project structure at a practical level.

## Root

- `app/` — backend core, orchestration, API, storage, tools, tests
- `frontend/` — operator console UI
- `docs/` — architecture, sprint plan, setup, continuity
- `README.md` — public project landing page
- `requirements.txt` — backend Python dependencies
- `.gitignore` — local/runtime ignore rules

## Backend

### `app/config.py`
Configuration for directories and LLM connectivity.

### `app/main.py`
CLI entrypoint.

### `app/agents/`
- `aether.py` — planning and action selection
- `scribe.py` — reporting
- `watcher.py` — observations, unresolved items, suggestions, memory logic

### `app/api/`
FastAPI service layer.

- `main.py` — API app and middleware
- `deps.py` — dependency providers
- `errors.py` — exception handling
- `response.py` — standard response envelope helper
- `schemas.py` — API request/response models
- `session_resolver.py` — API-side session resolution
- `routes/` — route handlers

### `app/core/`
Main operational spine.

- `intent_parser.py`
- `intent_router.py`
- `llm_client.py`
- `logger.py`
- `memory_service.py`
- `orchestrator.py`
- `session.py`
- `session_memory.py`
- `spectremind_core.py`
- `files.py`

### `app/parsers/`
- `nmap_parser.py`

### `app/reports/`
- `markdown.py`

### `app/schemas/`
- `intents.py`
- `responses.py`
- `tasks.py`

### `app/storage/`
- `db.py`
- `models.py`

### `app/tools/`
- `base.py`
- `registry.py`
- `tool_cards.py`
- `wrappers/nmap_wrapper.py`

### `app/tests/`
Backend and integration tests for parser, orchestration, storage, API, and memory flows.

## Frontend

### `frontend/public/brand/`
Brand assets used by the UI.

- `logo-mark.png`
- `icon-192.png`
- `favicon.ico`

### `frontend/src/app/`
- `layout.tsx` — metadata, global shell setup
- `page.tsx` — main operator console page
- `globals.css` — shared styles

### `frontend/src/components/layout/`
- `app-shell.tsx` — main page shell and branded header

### `frontend/src/components/sessions/`
- `session-sidebar.tsx` — session creation and switching

### `frontend/src/components/chat/`
- `chat-panel.tsx` — command surface and assistant cards

### `frontend/src/components/evidence/`
- `evidence-tabs.tsx`
- `findings-panel.tsx`
- `tool-runs-panel.tsx`
- `report-panel.tsx`
- `memory-panel.tsx`

### `frontend/src/lib/`
- `api.ts` — API client

### `frontend/src/types/`
- `api.ts` — shared frontend API types

## Docs

- `PROJECT_MODE_SOURCES.md`
- `SPECTREMIND_GOAL.md`
- `SPECTREMIND_SPRINT_PLAN.md`
- `SpectreMind_Project_Handoff.txt`
- `README.md`
- `PROJECT_FILE_MAP.md`
- `SETUP.md`
- `SCREENSHOTS.md`

## Runtime data

Runtime data should stay local and should not be tracked in Git.

Examples:
- databases
- generated sessions
- raw scan artifacts
- local environment files
