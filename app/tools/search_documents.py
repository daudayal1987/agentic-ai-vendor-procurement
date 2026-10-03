from __future__ import annotations

from typing import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.retrieval.dense import DenseRetriever
from app.retrieval.service import DocumentSearchService
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


def create_search_documents_tool(
    retriever_factory: Callable[[TenantContext], DenseRetriever],
    tenant_context: TenantContext,
) -> StructuredTool:
    """
    Create a tenant-scoped search_documents tool.
    """

    search_service = DocumentSearchService(
        retriever_factory=retriever_factory,
    )

    def search_documents(
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        return search_service.search(
            tenant_context=tenant_context,
            query=query,
            top_k=top_k,
        )

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