# SpectreMind Setup Guide

This guide covers the current local development flow for SpectreMind.

## Requirements

- Python 3.10+ or compatible installed
- Node.js and npm installed
- LM Studio installed for local LLM routing
- Nmap installed and available in PATH
- Git

## 1. Clone the repo

```bash
git clone https://github.com/1alikadri/Spectremind_AI.git
cd Spectremind_AI
```

## 2. Backend setup

### Create and activate a virtual environment

#### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install backend dependencies
```bash
pip install -r requirements.txt
```

## 3. Start the backend API

```bash
python -m uvicorn app.api.main:app --reload
```

Expected local API:
- `http://127.0.0.1:8000`

## 4. Frontend setup

```bash
cd frontend
npm install
```

Create a local environment file from the example:

### Windows
```bash
copy .env.example .env.local
```

### Linux / macOS
```bash
cp .env.example .env.local
```

Then run:

```bash
npm run dev
```

Expected local frontend:
- `http://localhost:3000`

## 5. LM Studio setup

Run LM Studio and load your model.

Recommended local server pattern:
- host: `http://127.0.0.1:1234`
- OpenAI-compatible endpoint enabled

Example model seen in current local setup:
- Qwen 3.5 9B (GGUF quantized in LM Studio)

## 6. Backend environment variables

These are the important backend variables:

- `LLM_API_BASE`
- `LLM_CHAT_COMPLETIONS_PATH`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `INTENT_ROUTER_ENABLED`
- `INTENT_ROUTER_MODEL`
- `INTENT_ROUTER_TIMEOUT_SECONDS`

Example:
```env
LLM_API_BASE=http://127.0.0.1:1234/v1
LLM_CHAT_COMPLETIONS_PATH=/chat/completions
LLM_MODEL=local-model
LLM_TIMEOUT_SECONDS=120
INTENT_ROUTER_ENABLED=1
INTENT_ROUTER_MODEL=local-model
INTENT_ROUTER_TIMEOUT_SECONDS=30
```

## 7. Frontend environment variable

In `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

## 8. Basic run flow

1. Start LM Studio and load the model
2. Start backend API with uvicorn
3. Start frontend with `npm run dev`
4. Open the operator console in the browser
5. Create or select a session
6. Issue a request in the command surface
7. Approve execution when required
8. Review evidence, report, and memory

## 9. Features visible in current UI

- branded operator header
- session sidebar
- command surface
- structured assistant output
- findings tab
- tool runs tab
- structured report
- global memory panel

## 10. Troubleshooting

### Backend API does not respond
- verify uvicorn is running
- verify port `8000`
- verify `NEXT_PUBLIC_API_BASE` matches the backend URL

### Frontend cannot reach backend
- check browser console/network
- confirm CORS settings
- confirm `.env.local` value

### LLM features fail
- confirm LM Studio server is running
- confirm the configured model is loaded
- confirm the OpenAI-compatible endpoint is reachable

### Nmap scan fails
- verify Nmap is installed
- verify it is available in PATH
- verify the target is valid and approved

## 11. Repo hygiene

Do not commit:
- `.env.local`
- local databases
- generated session artifacts
- `node_modules`
- `.next`
- temporary screenshot boards or scratch files
