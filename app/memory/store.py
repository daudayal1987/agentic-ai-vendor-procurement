from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Protocol


@dataclass(frozen=True)
class MemoryKey:
    """
    Identifies a long-term memory entry.

    Long-term memory is scoped independently from
    LangGraph's thread_id.
    """

    namespace: str
    key: str


class MemoryStore(Protocol):
    """
    Interface for persistent long-term memory.

    Implementations may later use PostgreSQL,
    Redis, LangGraph Store, etc.
    """

    def put(
        self,
        memory_key: MemoryKey,
        value: Any,
    ) -> None:
        ...

    def get(
        self,
        memory_key: MemoryKey,
    ) -> Any | None:
        ...

    def delete(
        self,
        memory_key: MemoryKey,
    ) -> None:
        ...


class InMemoryMemoryStore:
    """
    Simple process-local implementation.

    This is intentionally separate from LangGraph's
    InMemorySaver:

        InMemorySaver
            -> short-term conversation checkpoints

        InMemoryMemoryStore
            -> long-term memories
    """

    def __init__(self) -> None:
        self._data: dict[MemoryKey, Any] = {}
        self._lock = RLock()

    def put(
        self,
        memory_key: MemoryKey,
        value: Any,
    ) -> None:
        with self._lock:
            self._data[memory_key] = value

    def get(
        self,
        memory_key: MemoryKey,
    ) -> Any | None:
        with self._lock:
            return self._data.get(memory_key)

    def delete(
        self,
        memory_key: MemoryKey,
    ) -> None:
        with self._lock:
            self._data.pop(memory_key, None)