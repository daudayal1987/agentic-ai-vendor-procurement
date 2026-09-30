from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from app.agents.langgraph_react import (
    LangGraphReActAgent,
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


def test_graph_executes_tool_and_finishes() -> None:
    tool = make_tool()

    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
        tools=[tool],
        max_iterations=5,
    )

    result = agent.run(
        "What is the termination notice period?"
    )

    assert (
        result["answer"]
        == "The vendor termination notice period "
        "is 30 days."
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


def test_graph_passes_tool_observation_to_agent() -> None:
    tool = make_tool()

    bound_model = FakeBoundModel()

    agent = LangGraphReActAgent(
        model=FakeModel(bound_model),
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
    agent = LangGraphReActAgent(
        model=FakeModel(
            FakeBoundModel()
        ),
        tools=[make_tool()],
    )

    with pytest.raises(ValueError):
        agent.run("")


def test_max_iterations_protects_graph() -> None:
    agent = LangGraphReActAgent(
        model=AlwaysToolModel(),
        tools=[make_tool()],
        max_iterations=2,
    )

    with pytest.raises(RuntimeError):
        agent.run(
            "Keep searching forever."
        )


def test_unknown_tool_is_rejected() -> None:
    agent = LangGraphReActAgent(
        model=UnknownToolModel(),
        tools=[make_tool()],
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
        )


def test_invalid_max_iterations_is_rejected() -> None:
    with pytest.raises(ValueError):
        LangGraphReActAgent(
            model=FakeModel(
                FakeBoundModel()
            ),
            tools=[make_tool()],
            max_iterations=0,
        )