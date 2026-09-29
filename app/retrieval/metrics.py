from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    """
    Latency and result metrics for a retrieval operation.
    """

    embedding_latency_ms: float
    search_latency_ms: float
    total_latency_ms: float
    result_count: int