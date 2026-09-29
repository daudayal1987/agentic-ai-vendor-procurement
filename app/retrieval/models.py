from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class RetrievedChunk:
    """
    A document chunk returned by a retrieval operation.
    """

    chunk_id: UUID
    document_id: UUID
    tenant_id: UUID
    text: str
    section: str | None
    position: int
    token_count: int
    score: float
    source_metadata: dict[str, Any]