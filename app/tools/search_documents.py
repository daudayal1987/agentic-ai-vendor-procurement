from __future__ import annotations

from typing import Any, Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.retrieval.dense import DenseRetriever
from app.retrieval.models import RetrievedChunk
from app.tenants.context import TenantContext


class SearchDocumentsInput(BaseModel):
    """Input schema exposed to the LLM."""

    query: str = Field(
        min_length=1,
        description=(
            "Natural-language question or search query "
            "for the enterprise document collection."
        ),
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of evidence chunks to retrieve.",
    )


def _serialize_chunk(chunk: RetrievedChunk) -> dict[str, Any]:
    """Convert an internal retrieval result into a tool-safe structure."""

    return {
        "chunk_id": str(chunk.chunk_id),
        "document_id": str(chunk.document_id),
        "section": chunk.section,
        "position": chunk.position,
        "score": chunk.score,
        "text": chunk.text,
        "source_metadata": dict(chunk.source_metadata),
    }


def create_search_documents_tool(
    retriever_factory: Callable[[TenantContext], DenseRetriever],
    tenant_context: TenantContext,
) -> StructuredTool:
    """
    Create a tenant-scoped search_documents tool.

    The LLM controls only:
        - query
        - top_k

    Runtime code controls:
        - tenant_context
        - tenant_id
        - retriever
        - authorization context
    """

    def search_documents(
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search enterprise documents within the current tenant.

        Tenant identity is supplied by trusted runtime context and is
        never accepted from the LLM.
        """

        retriever = retriever_factory(tenant_context)

        results = retriever.retrieve(
            query=query,
            tenant_id=tenant_context.tenant_id,
            top_k=top_k,
        )

        return [
            _serialize_chunk(chunk)
            for chunk in results
        ]

    return StructuredTool.from_function(
        func=search_documents,
        name="search_documents",
        description=(
            "Search tenant-scoped enterprise documents and return "
            "relevant evidence chunks. Use this tool when the answer "
            "requires information from uploaded enterprise documents."
        ),
        args_schema=SearchDocumentsInput,
    )