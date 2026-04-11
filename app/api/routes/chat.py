from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_core
from app.api.schemas import AskRequest
from app.core.spectremind_core import SpectreMindCore
from app.api.schemas import ApiEnvelope, AskRequest
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ApiEnvelope)
def ask(request: AskRequest, core: SpectreMindCore = Depends(get_core)) -> dict:
    return core.handle(
        text=request.text,
        approved=request.approved,
        session_id=request.session_id,
        session_name=request.session_name,
        latest=request.latest,
    )