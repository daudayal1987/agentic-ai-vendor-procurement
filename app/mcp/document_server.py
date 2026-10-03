from __future__ import annotations

import asyncio
from uuid import UUID

from mcp.server import MCPServer

from app.retrieval.service import DocumentSearchService
from app.tenants.context import TenantContext


# Initialize your server instance
server = MCPServer(
    name="document-mcp-server",
    title="Enterprise Document MCP Server",
    description="MCP server exposing tenant-scoped enterprise document capabilities.",
    version="0.1.0",
)


def create_search_service() -> DocumentSearchService:
    raise NotImplementedError(
        "Wire the existing DenseRetriever factory here."
    )


# 1. Use the clean decorator. 
# The server will automatically read the types (str, int) and docstring descriptions!
@server.tool(
    name="search_documents",
    description="Search tenant-scoped enterprise documents and return relevant evidence."
)
async def search_documents(
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """
    Search tenant-scoped enterprise documents.

    :param query: Natural-language search query.
    :param top_k: Maximum number of results.
    """

    """
    MCP adapter for tenant-scoped document search.

    IMPORTANT:
    Tenant identity is trusted runtime context.
    It is not supplied by the MCP caller.
    """

    tenant_context = TenantContext(
        tenant_id=UUID("00000000-0000-0000-0000-000000000001"),
        user_id=UUID("00000000-0000-0000-0000-000000000002"),
        roles=("user",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

    search_service = create_search_service()

    return search_service.search(
        tenant_context=tenant_context,
        query=query,
        top_k=top_k,
    )


async def main() -> None:
    await server.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())