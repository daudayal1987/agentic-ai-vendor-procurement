from __future__ import annotations

from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class DocumentMCPClient:
    """
    MCP client for the enterprise document MCP server.

    Day 1 implementation:
        - stdio transport
        - explicit server process
        - tool discovery
        - tool invocation
    """

    def __init__(
        self,
        server_script: Path,
    ) -> None:
        self.server_script = server_script

        self._exit_stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def connect(self) -> None:
        server_params = StdioServerParameters(
            command="python",
            args=[str(self.server_script)],
        )

        read_stream, write_stream = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        session = await self._exit_stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await session.initialize()

        self._session = session

    async def list_tools(self) -> list[Any]:
        session = self._require_session()

        result = await session.list_tools()

        return list(result.tools)

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        session = self._require_session()

        return await session.call_tool(
            name,
            arguments,
        )

    async def close(self) -> None:
        await self._exit_stack.aclose()

    def _require_session(self) -> ClientSession:
        if self._session is None:
            raise RuntimeError(
                "MCP client is not connected"
            )

        return self._session