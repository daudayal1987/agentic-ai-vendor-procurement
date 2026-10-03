from typing import Any, Callable

from app.retrieval.dense import DenseRetriever
from app.retrieval.models import RetrievedChunk
from app.tenants.context import TenantContext


def serialize_retrieved_chunk(
    chunk: RetrievedChunk,
) -> dict[str, Any]:
    return {
        "chunk_id": str(chunk.chunk_id),
        "document_id": str(chunk.document_id),
        "section": chunk.section,
        "position": chunk.position,
        "score": chunk.score,
        "text": chunk.text,
        "source_metadata": dict(chunk.source_metadata),
    }


class DocumentSearchService:
    def __init__(
        self,
        retriever_factory: Callable[[TenantContext], DenseRetriever],
    ) -> None:
        self.retriever_factory = retriever_factory

    def search(
        self,
        *,
        tenant_context: TenantContext,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        retriever = self.retriever_factory(tenant_context)

        results = retriever.retrieve(
            query=query,
            tenant_id=tenant_context.tenant_id,
            top_k=top_k,
        )

        return [
            serialize_retrieved_chunk(chunk)
            for chunk in results
        ]