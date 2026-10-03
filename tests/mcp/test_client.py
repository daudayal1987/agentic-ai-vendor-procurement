from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.mcp.client import DocumentMCPClient
from app.mcp.document_server import create_document_mcp_server
from app.mcp.request_context import MCPRequestContext, RequestContextSigner
from app.retrieval.models import RetrievedChunk

TENANT_A = UUID("11111111-1111-1111-1111-111111111111")
SECRET = b"test-mcp-secret"


def make_context() -> MCPRequestContext:
    return MCPRequestContext(
        tenant_id=TENANT_A,
        user_id=uuid4(),
        roles=("ANALYST",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )


def make_chunk() -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        tenant_id=TENANT_A,
        text="termination",
        section="Termination",
        position=0,
        token_count=1,
        score=0.9,
        source_metadata={},
    )


class RecordingRetriever:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def retrieve(self, query: str, *, top_k=None, tenant_id=None):
        self.calls.append({"query": query, "top_k": top_k, "tenant_id": tenant_id})
        return [make_chunk()]


@pytest.mark.anyio
async def test_client_discovers_tools_and_calls_without_tenant_argument() -> None:
    retriever = RecordingRetriever()
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=signer,
    )

    client = DocumentMCPClient(
        server,
        identity_token=signer.issue(make_context()),
    )

    await client.connect()
    try:
        tools = await client.list_tools()
        assert [tool.name for tool in tools] == ["search_documents"]

        result = await client.call_tool(
            "search_documents",
            {"query": "termination", "top_k": 3},
        )

        assert result.is_error is False
        assert retriever.calls[-1]["tenant_id"] == TENANT_A
    finally:
        await client.close()


@pytest.mark.anyio
async def test_client_does_not_add_identity_to_tool_arguments() -> None:
    retriever = RecordingRetriever()
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=signer,
    )

    client = DocumentMCPClient(
        server,
        identity_token=signer.issue(make_context()),
    )

    await client.connect()
    try:
        await client.call_tool(
            "search_documents",
            {"query": "termination", "top_k": 3},
        )
    finally:
        await client.close()

    assert retriever.calls[-1] == {
        "query": "termination",
        "top_k": 3,
        "tenant_id": TENANT_A,
    }


@pytest.mark.anyio
async def test_client_requires_connection() -> None:
    signer = RequestContextSigner(SECRET)
    client = DocumentMCPClient(
        object(),
        identity_token=signer.issue(make_context()),
    )

    with pytest.raises(RuntimeError, match="not connected"):
        await client.list_tools()

    with pytest.raises(RuntimeError, match="not connected"):
        await client.call_tool("search_documents", {"query": "x"})
