from __future__ import annotations

from typing import Any, Sequence, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph


class AgentState(TypedDict):
    """State carried through the LangGraph workflow."""

    messages: list[BaseMessage]
    iterations: int
    events: list[dict[str, Any]]


class LangGraphReActAgent:
    """
    Minimal LangGraph implementation of the Day 16 ReAct loop.

    Graph:

        START
          ↓
        agent
          ↓
        should_continue
        ↙          ↘
      tools       END
        ↓
      agent
        ↓
      ...

    Runtime controls:
        - registered tools
        - tool execution
        - iteration limit

    The graph state contains messages and observable events.
    Private model reasoning is not intentionally stored.
    """

    def __init__(self,model: Any,tools: Sequence[BaseTool],*,max_iterations: int = 5,) -> None:
        if max_iterations <= 0:
            raise ValueError(
                "max_iterations must be greater than zero"
            )

        tool_list = list(tools)

        tool_names = [
            tool.name
            for tool in tool_list
        ]

        if len(tool_names) != len(set(tool_names)):
            raise ValueError(
                "Tool names must be unique"
            )

        self._model = model.bind_tools(tool_list)

        self._tools = {
            tool.name: tool
            for tool in tool_list
        }

        self._max_iterations = max_iterations

        builder = StateGraph(AgentState)

        builder.add_node(
            "agent",
            self._agent_node,
        )

        builder.add_node(
            "tools",
            self._tool_node,
        )

        builder.add_edge(
            START,
            "agent",
        )

        builder.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "end": END,
            },
        )

        builder.add_edge(
            "tools",
            "agent",
        )

        self._graph = builder.compile()

    def run(self,question: str,) -> dict[str, Any]:
        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        initial_state: AgentState = {
            "messages": [
                HumanMessage(
                    content=question.strip()
                )
            ],
            "iterations": 0,
            "events": [],
        }

        result = self._graph.invoke(
            initial_state
        )

        messages = result["messages"]

        final_message = messages[-1]

        if not isinstance(
            final_message,
            AIMessage,
        ):
            raise TypeError(
                "Graph did not finish with an AIMessage"
            )

        if final_message.tool_calls:
            raise RuntimeError(
                "Graph finished while a tool call "
                "was still pending"
            )

        return {
            "answer": _message_text(
                final_message
            ),
            "iterations": result["iterations"],
            "events": tuple(
                result["events"]
            ),
        }

    def _agent_node(self,state: AgentState,) -> dict[str, Any]:
        next_iteration = state["iterations"] + 1

        if next_iteration > self._max_iterations:
            raise RuntimeError(
                "LangGraph agent reached "
                "max_iterations without "
                "producing a final answer"
            )

        response = self._model.invoke(
            state["messages"]
        )

        if not isinstance(
            response,
            AIMessage,
        ):
            raise TypeError(
                "The bound model must return "
                "an AIMessage"
            )

        events = list(
            state["events"]
        )

        if response.tool_calls:
            for tool_call in response.tool_calls:
                events.append(
                    {
                        "event_type": "tool_call",
                        "iteration": next_iteration,
                        "tool_name": tool_call["name"],
                        "tool_call_id": tool_call["id"],
                    }
                )
        else:
            events.append(
                {
                    "event_type": "agent_finish",
                    "iteration": next_iteration,
                }
            )

        return {
            "messages": [
                response
            ],
            "iterations": next_iteration,
            "events": events,
        }

    def _tool_node(self,state: AgentState) -> dict[str, Any]:
        messages = state["messages"]

        last_message = messages[-1]

        if not isinstance(
            last_message,
            AIMessage,
        ):
            raise TypeError(
                "Tool node expected the previous "
                "message to be an AIMessage"
            )

        tool_messages: list[ToolMessage] = []
        events = list(
            state["events"]
        )

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_call_id = tool_call["id"]

            tool = self._tools.get(
                tool_name
            )

            if tool is None:
                raise RuntimeError(
                    "Model requested an unregistered "
                    f"tool: {tool_name}"
                )

            try:
                result = tool.invoke(
                    tool_call["args"]
                )
            except Exception:
                observation = (
                    "Tool execution failed. "
                    "The requested action could not "
                    "be completed."
                )

                tool_messages.append(
                    ToolMessage(
                        content=observation,
                        tool_call_id=tool_call_id,
                    )
                )

                events.append(
                    {
                        "event_type": "tool_error",
                        "iteration": state["iterations"],
                        "tool_name": tool_name,
                        "tool_call_id": tool_call_id,
                    }
                )

                continue

            tool_messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                )
            )

            events.append(
                {
                    "event_type": "tool_result",
                    "iteration": state["iterations"],
                    "tool_name": tool_name,
                    "tool_call_id": tool_call_id,
                }
            )

        return {
            "messages": tool_messages,
            "events": events,
        }

    @staticmethod
    def _should_continue(state: AgentState,) -> str:
        last_message = state["messages"][-1]

        if not isinstance(
            last_message,
            AIMessage,
        ):
            raise TypeError(
                "Routing expected the latest "
                "message to be an AIMessage"
            )

        if last_message.tool_calls:
            return "tools"

        return "end"


def _message_text(message: AIMessage,) -> str:
    content = message.content

    if isinstance(
        content,
        str,
    ):
        return content.strip()

    return str(content).strip()