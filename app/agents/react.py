from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool


@dataclass(frozen=True)
class ReActEvent:
    """
    Observable event generated during a ReAct run.

    Private model reasoning is deliberately not stored or exposed.
    """

    event_type: str
    iteration: int
    tool_name: str | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ReActResult:
    """
    Final result returned by the ReAct agent.
    """

    answer: str
    iterations: int
    events: tuple[ReActEvent, ...] = field(
        default_factory=tuple
    )


class ReActAgent:
    """
    Minimal ReAct-style agent loop built on LangChain tool calling.

    Flow:

        User question
            ↓
        Model
            ↓
        Tool decision
            ↓
        Tool execution
            ↓
        Observation
            ↓
        Model
            ↓
        Repeat or final answer

    The model decides whether a tool/action is needed.

    The runtime controls:
        - available tools
        - tool execution
        - iteration limits

    Private chain-of-thought is never exposed or persisted.
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

    def run(self,question: str,) -> ReActResult:
        """
        Execute the ReAct loop.

        The loop terminates when the model returns an AIMessage
        without tool calls.
        """

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        messages: list[BaseMessage] = [
            HumanMessage(
                content=question.strip()
            )
        ]

        events: list[ReActEvent] = []

        for iteration in range(1, self._max_iterations + 1):
            response = self._model.invoke(messages)

            if not isinstance(response, AIMessage):
                raise TypeError(
                    "The bound model must return an AIMessage"
                )

            # No tool call means the model has decided
            # that it can provide the final answer.
            if not response.tool_calls:
                events.append(
                    ReActEvent(
                        event_type="agent_finish",
                        iteration=iteration,
                    )
                )

                return ReActResult(
                    answer=_message_text(
                        response
                    ),
                    iterations=iteration,
                    events=tuple(events),
                )

            # Preserve the model's tool-call message in
            # the conversation history.
            messages.append(
                response
            )

            # A model response may contain multiple tool calls.
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_call_id = tool_call["id"]

                events.append(
                    ReActEvent(
                        event_type="tool_call",
                        iteration=iteration,
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                    )
                )

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
                    # Do not expose raw internal exception
                    # details to the model.
                    observation = (
                        "Tool execution failed. "
                        "The requested action could not "
                        "be completed."
                    )

                    messages.append(
                        ToolMessage(
                            content=observation,
                            tool_call_id=tool_call_id,
                        )
                    )

                    events.append(
                        ReActEvent(
                            event_type="tool_error",
                            iteration=iteration,
                            tool_name=tool_name,
                            tool_call_id=tool_call_id,
                        )
                    )

                    continue

                # Tool result becomes the ReAct observation.
                messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call_id,
                    )
                )

                events.append(
                    ReActEvent(
                        event_type="tool_result",
                        iteration=iteration,
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                    )
                )

        # Prevent an uncontrolled/infinite agent loop.
        raise RuntimeError(
            "ReAct agent reached max_iterations "
            "without producing a final answer"
        )


def _message_text(
    message: AIMessage,
) -> str:
    """
    Extract final textual content.

    Only final answer content is returned. Private reasoning
    is not intentionally exposed by this helper.
    """

    content = message.content

    if isinstance(
        content,
        str,
    ):
        return content.strip()

    return str(content).strip()