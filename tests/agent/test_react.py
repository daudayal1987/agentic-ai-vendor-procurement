from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from app.agents.react import ReActAgent


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
    Deterministic model used to test the ReAct loop.

    First invocation:
        request a tool

    Second invocation:
        return final answer
    """

    def __init__(self) -> None:
        self.invocations = 0
        self.messages: list[list[Any]] = []

    def invoke(
        self,
        messages: list[Any],
    ) -> AIMessage:
        self.invocations += 1
        self.messages.append(
            messages
        )

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
                "The vendor termination notice period "
                "is 30 days."
            )
        )


class FakeModel:
    """
    Fake model exposing the same bind_tools contract
    used by the real LangChain chat model.
    """

    def __init__(
        self,
        bound_model: FakeBoundModel,
    ) -> None:
        self.bound_model = bound_model
        self.bound_tools: list[Any] = []

    def bind_tools(
        self,
        tools: list[Any],
    ) -> FakeBoundModel:
        self.bound_tools = tools
        return self.bound_model


class AlwaysToolModel:
    """
    Model that continuously requests a tool.

    Used to verify max_iterations protection.
    """

    def bind_tools(
        self,
        tools: list[Any],
    ) -> AlwaysToolModel:
        self.tools = tools
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
    Model that requests a tool which was not registered.
    """

    def bind_tools(
        self,
        tools: list[Any],
    ) -> UnknownToolModel:
        self.tools = tools
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


def test_react_agent_executes_tool_and_finishes() -> None:
    tool = make_tool()

    bound_model = FakeBoundModel()

    model = FakeModel(
        bound_model
    )

    agent = ReActAgent(
        model=model,
        tools=[tool],
        max_iterations=5,
    )

    result = agent.run(
        "What is the termination notice period?"
    )

    assert (
        result.answer
        == "The vendor termination notice period is 30 days."
    )

    assert result.iterations == 2

    event_types = [
        event.event_type
        for event in result.events
    ]

    assert event_types == [
        "tool_call",
        "tool_result",
        "agent_finish",
    ]

    assert (
        result.events[0].tool_name
        == "search_documents"
    )

    assert (
        result.events[1].tool_name
        == "search_documents"
    )


def test_react_agent_passes_observation_back_to_model() -> None:
    tool = make_tool()

    bound_model = FakeBoundModel()

    model = FakeModel(
        bound_model
    )

    agent = ReActAgent(
        model=model,
        tools=[tool],
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
    tool = make_tool()

    model = FakeModel(
        FakeBoundModel()
    )

    agent = ReActAgent(
        model=model,
        tools=[tool],
    )

    with pytest.raises(ValueError):
        agent.run("")


def test_max_iterations_prevents_infinite_loop() -> None:
    tool = make_tool()

    agent = ReActAgent(
        model=AlwaysToolModel(),
        tools=[tool],
        max_iterations=2,
    )

    with pytest.raises(RuntimeError):
        agent.run(
            "Keep searching forever."
        )


def test_unregistered_tool_is_rejected() -> None:
    tool = make_tool()

    agent = ReActAgent(
        model=UnknownToolModel(),
        tools=[tool],
    )

    with pytest.raises(RuntimeError):
        agent.run(
            "Delete all enterprise documents."
        )


def test_duplicate_tool_names_are_rejected() -> None:
    first_tool = make_tool(
        name="search_documents"
    )

    second_tool = make_tool(
        name="search_documents"
    )

    model = FakeModel(
        FakeBoundModel()
    )

    with pytest.raises(ValueError):
        ReActAgent(
            model=model,
            tools=[
                first_tool,
                second_tool,
            ],
        )


def test_invalid_max_iterations_is_rejected() -> None:
    tool = make_tool()

    model = FakeModel(
        FakeBoundModel()
    )

    with pytest.raises(ValueError):
        ReActAgent(
            model=model,
            tools=[tool],
            max_iterations=0,
        )