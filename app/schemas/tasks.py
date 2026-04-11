# app/schemas/tasks.py
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import UTC, datetime
import uuid


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    objective: str
    target: Optional[str] = None
    category: Literal["recon", "reporting", "unknown"] = "unknown"
    approved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))