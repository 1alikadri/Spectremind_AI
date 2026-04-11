# SpectreMind Frontend

This frontend is the operator console for SpectreMind.

It is a Next.js application that talks to the SpectreMind FastAPI backend and exposes the live operator workflow through a structured interface.

## What the frontend does

The console provides:

- **Sessions panel** for engagement selection and creation
- **Command Surface** for natural-language interaction
- **Active Engagement** header with selected session context
- **Evidence** tabs for findings, tool runs, reports, and global memory
- **Structured output** disclosure for inspecting assistant response metadata

## Key UI areas

### Session sidebar
Shows current and recent engagements, status, finding counts, run counts, and memory presence.

### Command surface
Used to send requests such as:

- `show sessions`
- `show session`
- `show findings`
- `show tool runs`
- `show report`
- `scan hackthissite.org`

Execution-sensitive requests are paired with explicit approval.

### Evidence tabs
The evidence area includes:

- **Findings**
- **Tool Runs**
- **Report**
- **Global Memory**

### Structured report view
Reports are rendered as operator-facing cards instead of raw markdown dumps.

### Global memory
Global memory is intentionally presented as long-term operator memory across engagements, while saved notes may still preserve source-session linkage.

## Screenshots

Expected repo path for images: `../docs/images/`

![Operator Console](../docs/images/operator-console.png)
![Structured Report](../docs/images/structured-report.png)
![Global Memory](../docs/images/global-memory-panel.png)

## Local development

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment
Create `.env.local` from `.env.example` and set the backend API URL.

### 3. Run dev server
```bash
npm run dev
```

The app should start on:

- `http://localhost:3000`

## Environment variable

### `NEXT_PUBLIC_API_BASE`
Base URL for the SpectreMind FastAPI backend.

Example:
```env
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

## Backend expectation

The backend should be running before the UI is used, for example:

```bash
python -m uvicorn app.api.main:app --reload
```

## Files of interest

- `src/app/layout.tsx`
- `src/app/page.tsx`
- `src/components/layout/app-shell.tsx`
- `src/components/sessions/session-sidebar.tsx`
- `src/components/chat/chat-panel.tsx`
- `src/components/evidence/*`
- `src/lib/api.ts`
- `src/types/api.ts`

## Notes

This frontend is part of a local-first operator-controlled system. It should preserve clarity, control, and evidence visibility rather than behave like a casual chatbot UI.
