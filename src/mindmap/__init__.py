"""Research implementation of NCM³-E epistemic-temporal branch memory."""

from .model import EventKind, MemoryEvent, MemoryQuery, QueryKind, UNKNOWN
from .store import EpistemicBranchStore, Resolution, SYSTEM_CONFIGS

__all__ = [
    "EventKind",
    "MemoryEvent",
    "MemoryQuery",
    "QueryKind",
    "UNKNOWN",
    "EpistemicBranchStore",
    "Resolution",
    "SYSTEM_CONFIGS",
]
