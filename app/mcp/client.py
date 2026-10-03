from __future__ import annotations

from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from app.mcp.request_context import request_context_to_meta


class DocumentMCPClient:
    """Application wrapper around the MCP 2.x high-level Client."""

    def __init__(
        self,
        server: str | StdioServerParameters | Any,
        *,
        identity_token: str,
    ) -> None:
        if not identity_token:
            raise ValueError("identity_token must not be empty")

        self._client = Client(server)
        self._identity_token = identity_token
        self._connected = False

    async def connect(self) -> None:
        await self._client.__aenter__()
        self._connected = True

    async def list_tools(self) -> list[Any]:
        self._require_connected()
        result = await self._client.list_tools()
        return list(result.tools)

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        self._require_connected()
        return await self._client.call_tool(
            name,
            arguments,
            meta=request_context_to_meta(self._identity_token),
        )

    async def close(self) -> None:
        if self._connected:
            await self._client.__aexit__(None, None, None)
            self._connected = False

    def _require_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("MCP client is not connected")
