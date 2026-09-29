from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class VectorSearchResult:
    """
    Result returned by a vector index search.
    """

    vector_id: int
    score: float


@dataclass(frozen=True)
class IndexedChunk:
    """
    Application-level mapping between a vector ID and its document chunk.

    FAISS knows only about numeric vector IDs. This model preserves the
    business/document metadata required by the application.
    """

    vector_id: int
    chunk_id: UUID
    document_id: UUID
    tenant_id: UUID
    text: str
    section: str | None
    position: int
    token_count: int
    source_metadata: dict[str, Any]