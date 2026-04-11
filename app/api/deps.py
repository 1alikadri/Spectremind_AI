from __future__ import annotations

from app.core.memory_service import MemoryService
from app.core.spectremind_core import SpectreMindCore


_core = SpectreMindCore()
_memory = MemoryService()


def get_core() -> SpectreMindCore:
    return _core


def get_memory() -> MemoryService:
    return _memory