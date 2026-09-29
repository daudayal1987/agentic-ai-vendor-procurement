from __future__ import annotations

import pytest
from pydantic import ValidationError

from uuid import UUID, uuid4

from app.retrieval.models import RetrievedChunk
from app.tenants.context import TenantContext
from app.tools.search_documents import (
    SearchDocumentsInput,
    create_search_documents_tool,
)


class FakeRetriever:
    def __init__(self, result: RetrievedChunk) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def retrieve(
        self,
        query: str,
        *,
        top_k: int | None = None,
        tenant_id: UUID | None = None,
    ) -> list[RetrievedChunk]:
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "tenant_id": tenant_id,
            }
        )

        return [self.result]


def make_context(tenant_id: UUID) -> TenantContext:
    return TenantContext(
        tenant_id=tenant_id,
        user_id=uuid4(),
        roles=("ANALYST",),
        permissions=("document:read", "analysis:run"),
    )


def make_chunk(tenant_id: UUID) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        tenant_id=tenant_id,
        text="The termination notice period is 30 days.",
        section="Termination",
        position=2,
        token_count=8,
        score=0.91,
        source_metadata={
            "page": 4,
            "source_type": "pdf",
        },
    )


def test_input_schema_validates_query_and_top_k() -> None:
    data = SearchDocumentsInput(
        query="termination notice",
        top_k=3,
    )

    assert data.query == "termination notice"
    assert data.top_k == 3


def test_input_schema_rejects_empty_query() -> None:
    with pytest.raises(ValidationError):
        SearchDocumentsInput(query="", top_k=5)


def test_input_schema_rejects_invalid_top_k() -> None:
    for value in (0, 21):
        with pytest.raises(ValidationError):
            SearchDocumentsInput(query="termination", top_k=value)


def test_tool_exposes_only_query_and_top_k() -> None:
    tenant_id = uuid4()
    context = make_context(tenant_id)
    retriever = FakeRetriever(make_chunk(tenant_id))

    tool = create_search_documents_tool(
        retriever_factory=lambda _: retriever,
        tenant_context=context,
    )

    schema = tool.args_schema.model_json_schema()
    properties = schema["properties"]

    assert set(properties) == {"query", "top_k"}
    assert "tenant_id" not in properties
    assert "user_id" not in properties
    assert "permissions" not in properties


def test_tool_passes_runtime_tenant_to_retriever() -> None:
    tenant_id = uuid4()
    context = make_context(tenant_id)
    retriever = FakeRetriever(make_chunk(tenant_id))

    tool = create_search_documents_tool(
        retriever_factory=lambda received_context: (
            retriever
        ),
        tenant_context=context,
    )

    result = tool.invoke(
        {
            "query": "termination notice",
            "top_k": 3,
        }
    )

    assert retriever.calls == [
        {
            "query": "termination notice",
            "top_k": 3,
            "tenant_id": tenant_id,
        }
    ]

    assert len(result) == 1


def test_tool_serializes_retrieved_chunk() -> None:
    tenant_id = uuid4()
    context = make_context(tenant_id)

    chunk = make_chunk(tenant_id)
    retriever = FakeRetriever(chunk)

    tool = create_search_documents_tool(
        retriever_factory=lambda _: retriever,
        tenant_context=context,
    )

    result = tool.invoke(
        {
            "query": "termination notice",
            "top_k": 5,
        }
    )

    assert result == [
        {
            "chunk_id": str(chunk.chunk_id),
            "document_id": str(chunk.document_id),
            "section": "Termination",
            "position": 2,
            "score": 0.91,
            "text": "The termination notice period is 30 days.",
            "source_metadata": {
                "page": 4,
                "source_type": "pdf",
            },
        }
    ]


def test_tool_uses_default_top_k() -> None:
    tenant_id = uuid4()
    context = make_context(tenant_id)
    retriever = FakeRetriever(make_chunk(tenant_id))

    tool = create_search_documents_tool(
        retriever_factory=lambda _: retriever,
        tenant_context=context,
    )

    tool.invoke(
        {
            "query": "termination notice",
        }
    )

    assert retriever.calls[0]["top_k"] == 5