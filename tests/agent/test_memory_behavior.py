from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage

from app.agents.langgraph_react import LangGraphReActAgent
from app.memory.store import InMemoryMemoryStore, MemoryKey

from uuid import uuid4

from app.tenants.context import TenantContext


def make_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

class MemoryAwareModel:
    """
    Fake model used to test memory-aware behavior.

    The model follows a deterministic policy:
    - preference questions -> search memory
    - unrelated questions -> answer directly
    - after memory retrieval -> use the retrieved value
    """

    def __init__(self) -> None:
        self.invocations = 0
        self.tools: dict[str, Any] = {}
        self.messages: list[list[Any]] = []

    def bind_tools(
        self,
        tools: list[Any],
    ) -> "MemoryAwareModel":
        self.tools = {
            tool.name: tool
            for tool in tools
        }
        return self

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        self.invocations += 1
        self.messages.append(messages)

        last_message = messages[-1]

        # After search_memory has returned, use the result.
        if last_message.type == "tool":
            if last_message.content == "Python":
                return AIMessage(
                    content="You prefer Python."
                )

            return AIMessage(
                content="No preference found."
            )

        question = str(
            last_message.content
        ).lower()

        if "preferred language" in question:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_memory",
                        "args": {
                            "key": "preferred_language",
                        },
                        "id": "memory-search-1",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(
            content="This question does not require memory."
        )


class MemoryUpdatingModel:
    """
    Fake model that saves a durable user preference.
    """

    def __init__(self) -> None:
        self.invocations = 0
        self.tools: dict[str, Any] = {}

    def bind_tools(
        self,
        tools: list[Any],
    ) -> "MemoryUpdatingModel":
        self.tools = {
            tool.name: tool
            for tool in tools
        }
        return self

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        self.invocations += 1

        if self.invocations == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "save_memory",
                        "args": {
                            "key": "preferred_language",
                            "value": "Python",
                        },
                        "id": "memory-save-1",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(
            content="Preference saved."
        )


def test_relevant_question_searches_memory() -> None:
    store = InMemoryMemoryStore()

    store.put(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        ),
        "Python",
    )

    model = MemoryAwareModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[],
        memory_store=store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "What is my preferred language?",
        thread_id="thread-1",
    )

    assert result["answer"] == "You prefer Python."

    assert any(
        event["event_type"] == "tool_call"
        and event["tool_name"] == "search_memory"
        for event in result["events"]
    )


def test_retrieved_memory_affects_answer() -> None:
    store = InMemoryMemoryStore()

    store.put(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        ),
        "Python",
    )

    model = MemoryAwareModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[],
        memory_store=store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "What is my preferred language?",
        thread_id="thread-1",
    )

    assert result["answer"] == "You prefer Python."
    assert result["iterations"] == 2


def test_unrelated_question_does_not_search_memory() -> None:
    store = InMemoryMemoryStore()

    store.put(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        ),
        "Python",
    )

    model = MemoryAwareModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[],
        memory_store=store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "What is the capital of France?",
        thread_id="thread-1",
    )

    assert (
        result["answer"]
        == "This question does not require memory."
    )

    assert not any(
        event["tool_name"] == "search_memory"
        for event in result["events"]
        if event["event_type"] == "tool_call"
    )


def test_agent_can_save_new_memory() -> None:
    store = InMemoryMemoryStore()

    model = MemoryUpdatingModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[],
        memory_store=store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "Remember that my preferred language is Python.",
        thread_id="thread-1",
    )

    assert result["answer"] == "Preference saved."

    assert (
        store.get(
            MemoryKey(
                namespace="user-1",
                key="preferred_language",
            )
        )
        == "Python"
    )


def test_memory_update_replaces_existing_value() -> None:
    store = InMemoryMemoryStore()

    store.put(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        ),
        "Python",
    )

    model = MemoryUpdatingModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[],
        memory_store=store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    agent.run(
        "Remember that my preferred language is Python.",
        thread_id="thread-1",
    )

    assert (
        store.get(
            MemoryKey(
                namespace="user-1",
                key="preferred_language",
            )
        )
        == "Python"
    )