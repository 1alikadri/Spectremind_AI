from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routes import chat, chat_history, findings, memory, reports, sessions, tool_runs
from app.api.schemas import HealthResponse
from app.storage.db import init_db

init_db()

app = FastAPI(
    title="SpectreMind API",
    version="0.1.0",
    description="FastAPI service layer for SpectreMind.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "SPECTREMIND_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(findings.router)
app.include_router(tool_runs.router)
app.include_router(reports.router)
app.include_router(memory.router)
app.include_router(chat_history.router)

@app.get("/", tags=["default"])
def root() -> dict:
    return {
        "status": "handled",
        "summary": "SpectreMind API online.",
        "data": {
            "docs": "/docs",
            "health": "/health",
        },
        "next_steps": [],
    }

@app.get("/health", tags=["default"], response_model=HealthResponse)
def health() -> dict:
    return {
        "status": "ok",
        "service": "spectremind-api",
    }