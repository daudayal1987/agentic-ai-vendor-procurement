from __future__ import annotations

from pydantic import Field
from typing import Callable

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from app.mcp.request_context import RequestContextSigner, get_request_context, request_identity_middleware
from app.retrieval.dense import DenseRetriever
from app.retrieval.service import DocumentSearchService
from app.tenants.context import TenantContext


def create_document_mcp_server(
    *,
    retriever_factory: Callable[[TenantContext], DenseRetriever],
    signer: RequestContextSigner,
) -> MCPServer:
    """Create one long-lived, tenant-independent document MCP server."""

    server = MCPServer(
        name="document-mcp-server",
        title="Enterprise Document MCP Server",
        description="MCP server exposing tenant-scoped enterprise document capabilities.",
        version="0.1.0",
    )

    server.middleware.append(
        lambda ctx, call_next: request_identity_middleware(
            ctx,
            call_next,
            signer=signer,
        )
    )

    search_service = DocumentSearchService(retriever_factory=retriever_factory)

    @server.tool(
        name="search_documents",
        description=(
            "Search tenant-scoped enterprise documents "
            "and return relevant evidence."
        ),
    )
    async def search_documents(
        query: str = Field(
            min_length=1,
            description="Natural-language document search query.",
        ),
        top_k: int = Field(
            default=5,
            ge=1,
            le=50,
            description="Maximum number of results to return.",
        ),
        ctx: Context | None = None,
    ) -> list[dict]:
        """Search documents using the authenticated request identity.

        `ctx` is injected by MCP and is not part of the model-visible input
        schema. Tenant/user identity comes exclusively from middleware-bound
        authenticated state.
        """
        if ctx is None:
            raise RuntimeError("MCP request context is required")

        application_context = get_request_context()
        return search_service.search(
            tenant_context=application_context.to_tenant_context(),
            query=query,
            top_k=top_k,
        )

    return server
