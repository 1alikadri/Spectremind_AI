from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "summary": str(exc.detail),
                "data": {},
                "next_steps": [],
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "summary": "Request validation failed.",
                "data": {
                    "errors": exc.errors(),
                },
                "next_steps": [],
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled API exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "summary": "Internal server error.",
                "data": {},
                "next_steps": [],
            },
        )