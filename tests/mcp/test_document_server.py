from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from mcp import Client, MCPError

from app.mcp.document_server import create_document_mcp_server
from app.mcp.request_context import MCPRequestContext, RequestContextSigner, request_context_to_meta
from app.retrieval.models import RetrievedChunk

TENANT_A = UUID("11111111-1111-1111-1111-111111111111")
TENANT_B = UUID("22222222-2222-2222-2222-222222222222")
SECRET = b"test-mcp-secret"


def make_context(tenant_id: UUID) -> MCPRequestContext:
    return MCPRequestContext(
        tenant_id=tenant_id,
        user_id=uuid4(),
        roles=("ANALYST",),
        permissions=("document:read",),
        enabled_services=("document_search",),
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
        source_metadata={"page": 4, "source_type": "pdf"},
    )


class FakeRetriever:
    def __init__(self, tenant_id: UUID) -> None:
        self.tenant_id = tenant_id
        self.calls: list[dict[str, object]] = []

    def retrieve(self, query: str, *, top_k=None, tenant_id=None):
        self.calls.append({"query": query, "top_k": top_k, "tenant_id": tenant_id})
        return [make_chunk(tenant_id)]


class FailingRetriever:
    def retrieve(self, query: str, *, top_k=None, tenant_id=None):
        raise RuntimeError("retrieval backend unavailable")


async def call_with_identity(server, signer, context, arguments):
    token = signer.issue(context)
    async with Client(server) as client:
        return await client.call_tool(
            "search_documents",
            arguments,
            meta=request_context_to_meta(token),
        )


@pytest.mark.anyio
async def test_tool_is_registered_without_tenant_argument() -> None:
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: FakeRetriever(TENANT_A),
        signer=signer,
    )

    async with Client(server) as client:
        result = await client.list_tools()

    tool = next(tool for tool in result.tools if tool.name == "search_documents")
    assert "tenant_id" not in tool.input_schema["properties"]
    assert "query" in tool.input_schema["properties"]
    assert "top_k" in tool.input_schema["properties"]


@pytest.mark.anyio
async def test_search_uses_authenticated_tenant() -> None:
    retriever = FakeRetriever(TENANT_A)
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=signer,
    )

    result = await call_with_identity(
        server,
        signer,
        make_context(TENANT_A),
        {"query": "termination", "top_k": 3},
    )

    assert result.is_error is False
    assert retriever.calls[-1]["tenant_id"] == TENANT_A


@pytest.mark.anyio
async def test_same_server_processes_different_tenants() -> None:
    seen: list[UUID] = []

    class RecordingRetriever:
        def retrieve(self, query: str, *, top_k=None, tenant_id=None):
            seen.append(tenant_id)
            return [make_chunk(tenant_id)]

    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: RecordingRetriever(),
        signer=signer,
    )

    await call_with_identity(server, signer, make_context(TENANT_A), {"query": "a"})
    await call_with_identity(server, signer, make_context(TENANT_B), {"query": "b"})

    assert seen == [TENANT_A, TENANT_B]


@pytest.mark.anyio
async def test_missing_identity_is_rejected_before_tool_execution() -> None:
    retriever = FakeRetriever(TENANT_A)
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=signer,
    )

    async with Client(server) as client:
        with pytest.raises(MCPError, match="trusted application request context"):
            await client.call_tool("search_documents", {"query": "termination"})

    assert retriever.calls == []


@pytest.mark.anyio
async def test_invalid_signature_is_rejected_before_tool_execution() -> None:
    retriever = FakeRetriever(TENANT_A)
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=signer,
    )

    token = signer.issue(make_context(TENANT_A))
    payload, signature = token.split(".")
    bad_signature = ("A" if signature[0] != "A" else "B") + signature[1:]

    async with Client(server) as client:
        with pytest.raises(MCPError, match="signature"):
            await client.call_tool(
                "search_documents",
                {"query": "termination"},
                meta=request_context_to_meta(f"{payload}.{bad_signature}"),
            )

    assert retriever.calls == []


@pytest.mark.anyio
async def test_tenant_tampering_without_resigning_is_rejected() -> None:
    retriever = FakeRetriever(TENANT_A)
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=signer,
    )

    token = signer.issue(make_context(TENANT_A))
    payload, signature = token.split(".")

    import base64
    import json

    padding = "=" * ((-len(payload)) % 4)
    data = json.loads(base64.urlsafe_b64decode(payload + padding))
    data["tenant_id"] = str(TENANT_B)
    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()

    async with Client(server) as client:
        with pytest.raises(MCPError, match="signature"):
            await client.call_tool(
                "search_documents",
                {"query": "termination"},
                meta=request_context_to_meta(f"{tampered_payload}.{signature}"),
            )

    assert retriever.calls == []


@pytest.mark.anyio
async def test_expired_identity_is_rejected() -> None:
    now = 1000
    issue_signer = RequestContextSigner(SECRET, ttl_seconds=10, clock=lambda: now)
    verify_signer = RequestContextSigner(SECRET, ttl_seconds=10, clock=lambda: now + 10)
    retriever = FakeRetriever(TENANT_A)
    server = create_document_mcp_server(
        retriever_factory=lambda _: retriever,
        signer=verify_signer,
    )

    token = issue_signer.issue(make_context(TENANT_A))

    async with Client(server) as client:
        with pytest.raises(MCPError, match="expired"):
            await client.call_tool(
                "search_documents",
                {"query": "termination"},
                meta=request_context_to_meta(token),
            )

    assert retriever.calls == []


@pytest.mark.anyio
async def test_invalid_top_k_is_tool_error_result() -> None:
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: FakeRetriever(TENANT_A),
        signer=signer,
    )

    result = await call_with_identity(
        server,
        signer,
        make_context(TENANT_A),
        {"query": "termination", "top_k": 0},
    )

    assert result.is_error is True


@pytest.mark.anyio
async def test_empty_query_is_tool_error_result() -> None:
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: FakeRetriever(TENANT_A),
        signer=signer,
    )

    result = await call_with_identity(
        server,
        signer,
        make_context(TENANT_A),
        {"query": "", "top_k": 5},
    )

    assert result.is_error is True


@pytest.mark.anyio
async def test_retrieval_failure_is_sanitized_tool_error_result() -> None:
    signer = RequestContextSigner(SECRET)
    server = create_document_mcp_server(
        retriever_factory=lambda _: FailingRetriever(),
        signer=signer,
    )

    result = await call_with_identity(
        server,
        signer,
        make_context(TENANT_A),
        {"query": "termination"},
    )

    assert result.is_error is True
    assert "Error executing tool search_documents" in result.content[0].text
    assert "retrieval backend unavailable" not in result.content[0].text
