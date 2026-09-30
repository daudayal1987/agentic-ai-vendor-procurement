from __future__ import annotations

from typing import Any

from uuid import uuid4

from app.tenants.context import TenantContext

import pytest
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import StructuredTool

from app.agents.langgraph_react import (
    LangGraphReActAgent,
)

from app.memory.store import InMemoryMemoryStore, MemoryKey
from app.memory.tools import create_memory_tools 


def make_tenant_context() -> TenantContext:
    return TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

def make_tool(
    name: str = "search_documents",
) -> StructuredTool:
    def search_documents(
        query: str,
    ) -> str:
        return (
            f"Evidence found for query: {query}"
        )

    return StructuredTool.from_function(
        func=search_documents,
        name=name,
        description="Search enterprise documents.",
    )


class FakeBoundModel:
    """
    Fake model used to test the normal ReAct loop.
    """

    def __init__(self) -> None:
        self.invocations = 0
        self.messages: list[list[Any]] = []

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        self.invocations += 1
        self.messages.append(messages)

        if self.invocations == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_documents",
                        "args": {
                            "query": (
                                "vendor termination "
                                "notice period"
                            )
                        },
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(
            content=(
                "The vendor termination notice "
                "period is 30 days."
            )
        )


class FakeModel:
    """
    Mimics a LangChain model that supports bind_tools().
    """

    def __init__(
        self,
        bound_model: FakeBoundModel,
    ) -> None:
        self.bound_model = bound_model

    def bind_tools(
        self,
        tools: list[Any],
    ) -> FakeBoundModel:
        return self.bound_model


class AlwaysToolModel:
    """
    Model that always asks for a tool.

    Used to test max_iterations.
    """

    def bind_tools(
        self,
        tools: list[Any],
    ) -> AlwaysToolModel:
        return self

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_documents",
                    "args": {
                        "query": "termination",
                    },
                    "id": "loop-call",
                    "type": "tool_call",
                }
            ],
        )


class UnknownToolModel:
    """
    Model that asks for a tool that wasn't registered.
    """

    def bind_tools(
        self,
        tools: list[Any],
    ) -> UnknownToolModel:
        return self

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "delete_all_documents",
                    "args": {},
                    "id": "unknown-call",
                    "type": "tool_call",
                }
            ],
        )


class RecordingModel:
    """
    Records messages sent to the model.

    Used to verify short-term memory.
    """

    def __init__(self) -> None:
        self.messages: list[list[Any]] = []

    def bind_tools(
        self,
        tools: list[Any],
    ) -> RecordingModel:
        return self

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        self.messages.append(messages)

        return AIMessage(
            content="Done."
        )


class MemoryWritingModel:
    """
    First invocation:
        save_memory()

    Second invocation:
        final answer.
    """

    def __init__(self) -> None:
        self.invocations = 0
        self.tools: dict[str, Any] = {}

    def bind_tools(
        self,
        tools: list[Any],
    ) -> MemoryWritingModel:
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
            assert "save_memory" in self.tools

            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "save_memory",
                        "args": {
                            "key": "preferred_language",
                            "value": "Python",
                        },
                        "id": "memory-call-1",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(
            content="I saved your preference."
        )


class MemoryReadingModel:
    """
    First invocation:
        Ask the search_memory tool for the preference.

    Second invocation:
        Inspect the tool result and produce the answer.
    """

    def __init__(self) -> None:
        self.invocations = 0
        self.tools: dict[str, Any] = {}
        self.messages: list[list[Any]] = []

    def bind_tools(
        self,
        tools: list[Any],
    ) -> "MemoryReadingModel":
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

        # First model call:
        # ask the memory tool for the value.
        if self.invocations == 1:
            assert "search_memory" in self.tools

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

        # Second model call:
        # inspect the result returned by search_memory.
        tool_messages = [
            message
            for message in messages
            if message.type == "tool"
        ]

        assert tool_messages

        memory_value = tool_messages[-1].content

        if memory_value == "Python":
            return AIMessage(
                content="You prefer Python."
            )

        return AIMessage(
            content="No preference found."
        )


def test_graph_executes_tool_and_finishes() -> None:
    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[make_tool()],
        max_iterations=5,
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "What is the termination notice period?"
    )

    assert result["answer"] == (
        "The vendor termination notice "
        "period is 30 days."
    )

    assert result["iterations"] == 2

    event_types = [
        event["event_type"]
        for event in result["events"]
    ]

    assert event_types == [
        "tool_call",
        "tool_result",
        "agent_finish",
    ]


def test_graph_passes_tool_result_back_to_model() -> None:
    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[make_tool()],
        tenant_context=make_tenant_context(),
    )

    agent.run(
        "Find the termination notice period."
    )

    assert len(
        bound_model.messages
    ) == 2

    second_turn = bound_model.messages[1]

    assert any(
        message.type == "tool"
        for message in second_turn
    )


def test_empty_question_is_rejected() -> None:
    agent = LangGraphReActAgent(
        model=FakeModel(
            FakeBoundModel()
        ),
        tools=[make_tool()],
        tenant_context=make_tenant_context(),
    )

    with pytest.raises(ValueError):
        agent.run("")


def test_invalid_thread_id_is_rejected() -> None:
    agent = LangGraphReActAgent(
        model=FakeModel(
            FakeBoundModel()
        ),
        tools=[make_tool()],
        tenant_context=make_tenant_context(),
    )

    with pytest.raises(ValueError):
        agent.run(
            "Test question",
            thread_id="",
        )


def test_invalid_max_iterations_is_rejected() -> None:
    with pytest.raises(ValueError):
        LangGraphReActAgent(
            model=FakeModel(
                FakeBoundModel()
            ),
            tools=[make_tool()],
            max_iterations=0,
            tenant_context=make_tenant_context(),
        )


def test_max_iterations_protects_graph() -> None:
    agent = LangGraphReActAgent(
        model=AlwaysToolModel(),
        tools=[make_tool()],
        max_iterations=2,
        tenant_context=make_tenant_context(),
    )

    with pytest.raises(RuntimeError):
        agent.run(
            "Keep searching forever."
        )


def test_unknown_tool_is_rejected() -> None:
    agent = LangGraphReActAgent(
        model=UnknownToolModel(),
        tools=[make_tool()],
        tenant_context=make_tenant_context(),
    )

    with pytest.raises(RuntimeError):
        agent.run(
            "Delete all enterprise documents."
        )


def test_duplicate_tool_names_are_rejected() -> None:
    first = make_tool(
        name="search_documents"
    )

    second = make_tool(
        name="search_documents"
    )

    with pytest.raises(ValueError):
        LangGraphReActAgent(
            model=FakeModel(
                FakeBoundModel()
            ),
            tools=[first, second],
            tenant_context=make_tenant_context(),
        )


def test_same_thread_remembers_previous_message() -> None:
    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[make_tool()],
        tenant_context=make_tenant_context(),
    )

    agent.run(
        "Analyze Vendor X.",
        thread_id="vendor-analysis",
    )

    agent.run(
        "What about its SLA?",
        thread_id="vendor-analysis",
    )

    messages = bound_model.messages[-1]

    human_messages = [
        message
        for message in messages
        if message.type == "human"
    ]

    assert len(human_messages) == 2

    assert human_messages[0].content == (
        "Analyze Vendor X."
    )

    assert human_messages[1].content == (
        "What about its SLA?"
    )


def test_different_threads_do_not_share_history() -> None:
    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[make_tool()],
        tenant_context=make_tenant_context(),
    )

    agent.run(
        "Analyze Vendor X.",
        thread_id="thread-a",
    )

    agent.run(
        "What about its SLA?",
        thread_id="thread-b",
    )

    messages = bound_model.messages[-1]

    human_messages = [
        message
        for message in messages
        if message.type == "human"
    ]

    assert len(human_messages) == 1

    assert human_messages[0].content == (
        "What about its SLA?"
    )


def test_long_term_memory_tool_is_added() -> None:
    memory_store = InMemoryMemoryStore()

    model = MemoryWritingModel()

    LangGraphReActAgent(
        model=model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    assert "save_memory" in model.tools
    assert "search_memory" in model.tools


def test_agent_can_save_long_term_memory() -> None:
    memory_store = InMemoryMemoryStore()

    model = MemoryWritingModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "Remember that I prefer Python.",
        thread_id="thread-a",
    )

    assert result["answer"] == (
        "I saved your preference."
    )

    assert memory_store.get(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        )
    ) == "Python"


def test_agent_can_read_long_term_memory() -> None:
    memory_store = InMemoryMemoryStore()

    memory_store.put(
        MemoryKey(
            namespace="user-1",
            key="preferred_language",
        ),
        "Python",
    )

    model = MemoryReadingModel()

    agent = LangGraphReActAgent(
        model=model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = agent.run(
        "What language do I prefer?",
        thread_id="thread-b",
    )

    assert result["answer"] == (
        "You prefer Python."
    )

    assert model.invocations == 2

    second_turn = model.messages[1]

    assert any(
        message.type == "tool"
        and message.content == "Python"
        for message in second_turn
    )


def test_long_term_memory_survives_thread_change() -> None:
    memory_store = InMemoryMemoryStore()

    # Write through one agent/thread.
    writer_model = MemoryWritingModel()

    writer_agent = LangGraphReActAgent(
        model=writer_model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    writer_agent.run(
        "Remember that I prefer Python.",
        thread_id="thread-a",
    )

    # Read through a different agent/thread.
    reader_model = MemoryReadingModel()

    reader_agent = LangGraphReActAgent(
        model=reader_model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    result = reader_agent.run(
        "What language do I prefer?",
        thread_id="thread-b",
    )

    assert result["answer"] == (
        "You prefer Python."
    )


def test_users_have_isolated_long_term_memory() -> None:
    memory_store = InMemoryMemoryStore()

    # User 1 writes memory.
    writer_model = MemoryWritingModel()

    writer_agent = LangGraphReActAgent(
        model=writer_model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-1",
        tenant_context=make_tenant_context(),
    )

    writer_agent.run(
        "Remember that I prefer Python.",
        thread_id="user-1-thread",
    )

    # User 2 gets a separately scoped memory tool.
    reader_model = MemoryReadingModel()

    reader_agent = LangGraphReActAgent(
        model=reader_model,
        tools=[make_tool()],
        memory_store=memory_store,
        user_id="user-2",
        tenant_context=make_tenant_context(),
    )

    result = reader_agent.run(
        "What language do I prefer?",
        thread_id="user-2-thread",
    )

    assert result["answer"] == (
        "No preference found."
    )


def test_agent_blocks_unauthorized_tool_execution() -> None:
    executed = False

    def search_documents(query: str) -> str:
        nonlocal executed
        executed = True
        return "secret data"

    tool = StructuredTool.from_function(
        func=search_documents,
        name="search_documents",
        description="Search enterprise documents.",
    )

    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[tool],
        tenant_context=TenantContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            roles=("reviewer",),
            permissions=(),
            enabled_services=("document_search",),
        ),
    )

    result = agent.run(
        "Search the enterprise documents."
    )

    assert executed is False

    assert any(
        event["event_type"] == "policy_denied"
        for event in result["events"]
    )


def test_agent_executes_authorized_tool() -> None:
    executed = False

    def search_documents(query: str) -> str:
        nonlocal executed
        executed = True
        return "authorized data"

    tool = StructuredTool.from_function(
        func=search_documents,
        name="search_documents",
        description="Search enterprise documents.",
    )

    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[tool],
        tenant_context=TenantContext(
            tenant_id=uuid4(),
            user_id=uuid4(),
            roles=("analyst",),
            permissions=("document:read",),
            enabled_services=("document_search",),
        ),
    )

    result = agent.run(
        "Search the enterprise documents."
    )

    assert executed is True

    assert any(
        event["event_type"] == "tool_result"
        for event in result["events"]
    )