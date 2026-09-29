from __future__ import annotations

from time import perf_counter
from typing import Sequence
from uuid import UUID

from app.retrieval.config import RetrievalConfig
from app.retrieval.embeddings.interface import EmbeddingModel
from app.retrieval.metrics import RetrievalMetrics
from app.retrieval.models import RetrievedChunk
from app.retrieval.vector_store.interface import VectorIndex
from app.retrieval.vector_store.models import IndexedChunk


class DenseRetriever:
    """
    Dense semantic retriever backed by an embedding model and vector index.

    Tenant filtering is applied after vector search using trusted
    application-level tenant context.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_index: VectorIndex,
        indexed_chunks: Sequence[IndexedChunk],
        config: RetrievalConfig | None = None,
    ) -> None:
        if (
            embedding_model.dimension
            != vector_index.dimension
        ):
            raise ValueError(
                "embedding model dimension and vector index dimension "
                "must match"
            )

        self._embedding_model = embedding_model
        self._vector_index = vector_index
        self._config = (
            config
            or RetrievalConfig()
        )

        self._chunks_by_vector_id = {
            chunk.vector_id: chunk
            for chunk in indexed_chunks
        }

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        tenant_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        results, _ = self.retrieve_with_metrics(
            query,
            top_k=top_k,
            tenant_id=tenant_id,
        )

        return results

    def retrieve_with_metrics(
        self,
        query: str,
        *,
        top_k: int | None = None,
        tenant_id: UUID | None = None,
    ) -> tuple[list[RetrievedChunk], RetrievalMetrics]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError(
                "query must be a non-empty string"
            )

        resolved_top_k = (
            self._config.default_top_k
            if top_k is None
            else top_k
        )

        if resolved_top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero"
            )

        if resolved_top_k > self._config.max_top_k:
            raise ValueError(
                "top_k cannot exceed max_top_k"
            )

        total_start = perf_counter()

        embedding_start = perf_counter()

        query_embedding = (
            self._embedding_model.embed_query(
                query
            )
        )

        embedding_latency_ms = (
            perf_counter()
            - embedding_start
        ) * 1000

        search_start = perf_counter()

        search_results = self._vector_index.search(
            query_vector=query_embedding,
            top_k=resolved_top_k,
        )

        search_latency_ms = (
            perf_counter()
            - search_start
        ) * 1000

        retrieved: list[RetrievedChunk] = []

        for result in search_results:
            indexed_chunk = (
                self._chunks_by_vector_id.get(
                    result.vector_id
                )
            )

            if indexed_chunk is None:
                continue

            if (
                tenant_id is not None
                and indexed_chunk.tenant_id != tenant_id
            ):
                continue

            if (
                self._config.minimum_score is not None
                and result.score
                < self._config.minimum_score
            ):
                continue

            retrieved.append(
                RetrievedChunk(
                    chunk_id=indexed_chunk.chunk_id,
                    document_id=indexed_chunk.document_id,
                    tenant_id=indexed_chunk.tenant_id,
                    text=indexed_chunk.text,
                    section=indexed_chunk.section,
                    position=indexed_chunk.position,
                    token_count=indexed_chunk.token_count,
                    score=result.score,
                    source_metadata=dict(
                        indexed_chunk.source_metadata
                    ),
                )
            )

        total_latency_ms = (
            perf_counter()
            - total_start
        ) * 1000

        metrics = RetrievalMetrics(
            embedding_latency_ms=embedding_latency_ms,
            search_latency_ms=search_latency_ms,
            total_latency_ms=total_latency_ms,
            result_count=len(retrieved),
        )

        return retrieved, metrics