from app.memory.store import (
    InMemoryMemoryStore,
    MemoryKey,
)


def test_memory_can_be_stored_and_retrieved() -> None:
    store = InMemoryMemoryStore()

    key = MemoryKey(
        namespace="user-1",
        key="preferred_language",
    )

    store.put(
        key,
        "Python",
    )

    assert store.get(key) == "Python"


def test_missing_memory_returns_none() -> None:
    store = InMemoryMemoryStore()

    key = MemoryKey(
        namespace="user-1",
        key="preferred_language",
    )

    assert store.get(key) is None


def test_memory_can_be_updated() -> None:
    store = InMemoryMemoryStore()

    key = MemoryKey(
        namespace="user-1",
        key="preferred_language",
    )

    store.put(
        key,
        "Python",
    )

    store.put(
        key,
        "TypeScript",
    )

    assert store.get(key) == "TypeScript"


def test_memory_can_be_deleted() -> None:
    store = InMemoryMemoryStore()

    key = MemoryKey(
        namespace="user-1",
        key="preferred_language",
    )

    store.put(
        key,
        "Python",
    )

    store.delete(key)

    assert store.get(key) is None


def test_different_namespaces_are_isolated() -> None:
    store = InMemoryMemoryStore()

    user_a_key = MemoryKey(
        namespace="user-a",
        key="preferred_language",
    )

    user_b_key = MemoryKey(
        namespace="user-b",
        key="preferred_language",
    )

    store.put(
        user_a_key,
        "Python",
    )

    store.put(
        user_b_key,
        "Java",
    )

    assert store.get(user_a_key) == "Python"
    assert store.get(user_b_key) == "Java"


def test_different_keys_can_exist_in_same_namespace() -> None:
    store = InMemoryMemoryStore()

    language_key = MemoryKey(
        namespace="user-1",
        key="preferred_language",
    )

    timezone_key = MemoryKey(
        namespace="user-1",
        key="timezone",
    )

    store.put(
        language_key,
        "Python",
    )

    store.put(
        timezone_key,
        "Asia/Kolkata",
    )

    assert store.get(language_key) == "Python"
    assert store.get(timezone_key) == "Asia/Kolkata"