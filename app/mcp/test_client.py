from __future__ import annotations

import asyncio
from pathlib import Path

from app.mcp.client import DocumentMCPClient


async def main() -> None:
    server_script = (
        Path(__file__).resolve().parent
        / "document_server.py"
    )

    client = DocumentMCPClient(
        server_script=server_script,
    )

    try:
        await client.connect()

        tools = await client.list_tools()

        print("Discovered tools:")

        for tool in tools:
            print(
                f"- {tool.name}: "
                f"{tool.description}"
            )

        # result = await client.call_tool(
        #     "search_documents",
        #     {
        #         "query": "What is the termination clause?",
        #         "top_k": 5,
        #     },
        # )

        # print("\nTool result:")
        # print(result)

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())