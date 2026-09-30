from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool

from app.memory.store import MemoryKey, MemoryStore


def create_memory_tools(
    memory_store: MemoryStore,
    *,
    user_id: str,
) -> list[StructuredTool]:
    """
    Create memory tools scoped to one authenticated user.

    The model receives tools that cannot choose the namespace.
    The namespace is fixed by the application/user context.
    """

    if (
        not isinstance(user_id, str)
        or not user_id.strip()
    ):
        raise ValueError(
            "user_id must be a non-empty string"
        )

    namespace = user_id.strip()

    def save_memory(
        key: str,
        value: str,
    ) -> str:
        if not key.strip():
            raise ValueError(
                "Memory key must not be empty"
            )

        if not value.strip():
            raise ValueError(
                "Memory value must not be empty"
            )

        memory_store.put(
            MemoryKey(
                namespace=namespace,
                key=key.strip(),
            ),
            value.strip(),
        )

        return (
            f"Memory saved successfully under "
            f"'{key.strip()}'."
        )

    def search_memory(
        key: str,
    ) -> str:
        if not key.strip():
            raise ValueError(
                "Memory key must not be empty"
            )

        value = memory_store.get(
            MemoryKey(
                namespace=namespace,
                key=key.strip(),
            )
        )

        if value is None:
            return (
                f"No memory found for "
                f"'{key.strip()}'."
            )

        return str(value)

    return [
        StructuredTool.from_function(
            func=save_memory,
            name="save_memory",
            description=(
                "Save a durable fact or preference "
                "about the current user. Use this only "
                "when the information is useful beyond "
                "the current conversation."
            ),
        ),
        StructuredTool.from_function(
            func=search_memory,
            name="search_memory",
            description=(
                "Retrieve a previously saved durable "
                "memory for the current user."
            ),
        ),
    ]