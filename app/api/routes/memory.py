from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_memory
from app.api.response import api_response
from app.api.schemas import MemoryRecallRequest, MemorySaveRequest
from app.core.memory_service import MemoryService
from app.storage.db import get_latest_session_id, get_session_by_name
from app.api.schemas import ApiEnvelope, AskRequest
from app.api.session_resolver import resolve_optional_session_id

router = APIRouter(prefix="/memory", tags=["memory"])




@router.post("/save", response_model=ApiEnvelope)
def save_memory(request: MemorySaveRequest, memory: MemoryService = Depends(get_memory)) -> dict:
    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Memory content is required.")

    source_session_id = resolve_optional_session_id(
        session_id=request.session_id,
        session_name=request.session_name,
        latest=request.latest,
    )

    memory_id = memory.remember(
        memory_type=request.memory_type,
        content=content,
        source_session_id=source_session_id,
    )

    return api_response(
        status="handled",
        summary="Memory saved.",
        data={
            "memory_id": memory_id,
            "memory_type": request.memory_type,
            "content": content,
            "source_session_id": source_session_id,
        },
    )


@router.post("/recall", response_model=ApiEnvelope)
def recall_memory(request: MemoryRecallRequest, memory: MemoryService = Depends(get_memory)) -> dict:
    results = memory.recall(
        query=request.query,
        limit=request.limit,
        memory_type=request.memory_type,
    )

    return api_response(
        status="handled",
        summary=f"{len(results)} memory item(s) loaded.",
        data={
            "query": request.query,
            "memories": results,
        },
    )