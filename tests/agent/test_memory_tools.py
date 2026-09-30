from app.memory.store import (
    InMemoryMemoryStore,
    MemoryKey,
)
from app.memory.tools import create_memory_tools


def test_save_memory_writes_to_store() -> None:
    store = InMemoryMemoryStore()

    tools = create_memory_tools(
        store,
        user_id="user-1",
    )

    save_memory = next(
        tool
        for tool in tools
        if tool.name == "save_memory"
    )

    result = save_memory.invoke(
        {
            "key": "preferred_language",
            "value": "Python",
        }
    )

    assert result == (
        "Memory saved successfully under "
        "'preferred_language'."
    )

    assert store.get(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        )
    ) == "Python"


def test_search_memory_reads_from_store() -> None:
    store = InMemoryMemoryStore()

    store.put(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        ),
        "Python",
    )

    tools = create_memory_tools(
        store,
        user_id="user-1",
    )

    search_memory = next(
        tool
        for tool in tools
        if tool.name == "search_memory"
    )

    result = search_memory.invoke(
        {
            "key": "preferred_language",
        }
    )

    assert result == "Python"


def test_search_memory_returns_missing_message() -> None:
    store = InMemoryMemoryStore()

    tools = create_memory_tools(
        store,
        user_id="user-1",
    )

    search_memory = next(
        tool
        for tool in tools
        if tool.name == "search_memory"
    )

    result = search_memory.invoke(
        {
            "key": "preferred_language",
        }
    )

    assert result == (
        "No memory found for "
        "'preferred_language'."
    )


def test_memory_tool_is_scoped_to_user() -> None:
    store = InMemoryMemoryStore()

    user_a_tools = create_memory_tools(
        store,
        user_id="user-a",
    )

    user_b_tools = create_memory_tools(
        store,
        user_id="user-b",
    )

    user_a_save = next(
        tool
        for tool in user_a_tools
        if tool.name == "save_memory"
    )

    user_b_search = next(
        tool
        for tool in user_b_tools
        if tool.name == "search_memory"
    )

    user_a_save.invoke(
        {
            "key": "language",
            "value": "Python",
        }
    )

    result = user_b_search.invoke(
        {
            "key": "language",
        }
    )

    assert result == (
        "No memory found for 'language'."
    )


def test_empty_user_id_is_rejected() -> None:
    store = InMemoryMemoryStore()

    try:
        create_memory_tools(
            store,
            user_id="",
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_empty_memory_key_is_rejected() -> None:
    store = InMemoryMemoryStore()

    tools = create_memory_tools(
        store,
        user_id="user-1",
    )

    save_memory = next(
        tool
        for tool in tools
        if tool.name == "save_memory"
    )

    try:
        save_memory.invoke(
            {
                "key": "",
                "value": "Python",
            }
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )