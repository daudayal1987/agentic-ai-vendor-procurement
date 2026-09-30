from __future__ import annotations

from typing import Annotated, Any, Sequence, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages

from app.memory.store import (
    MemoryStore,
)
from app.memory.tools import create_memory_tools

MEMORY_BEHAVIOR_PROMPT = """
You have access to long-term memory for the current user.

Use search_memory when the user's question depends on a
durable user-specific fact, preference, or previous decision.

Use save_memory when the user explicitly provides information
that should remain useful in future conversations.

Do not use memory tools for questions that do not depend on
user-specific information.

When memory is retrieved, use the retrieved information as
context for your answer. Do not invent memories that were
not retrieved.
""".strip()


class AgentState(TypedDict):
    """State carried through the LangGraph workflow."""

    messages: Annotated[list[BaseMessage], add_messages]
    iterations: int
    events: list[dict[str, Any]]


class LangGraphReActAgent:
    """
    Simple LangGraph ReAct agent.

    Short-term memory:
        thread_id -> LangGraph checkpointer

    Long-term memory:
        user_id -> MemoryStore

    Memory is exposed to the model through ReAct tools:
        - save_memory
        - search_memory
    """

    def __init__(
        self,
        model: Any,
        tools: Sequence[BaseTool],
        *,
        max_iterations: int = 5,
        memory_store: MemoryStore | None = None,
        user_id: str | None = None,
    ) -> None:
        if max_iterations <= 0:
            raise ValueError(
                "max_iterations must be greater than zero"
            )

        if user_id is not None:
            if (
                not isinstance(user_id, str)
                or not user_id.strip()
            ):
                raise ValueError(
                    "user_id must be a non-empty string"
                )

        application_tools = list(tools)

        tool_names = [
            tool.name
            for tool in application_tools
        ]

        if len(tool_names) != len(set(tool_names)):
            raise ValueError(
                "Tool names must be unique"
            )

        self._max_iterations = max_iterations
        self._memory_store = memory_store
        self._user_id = user_id

        # Start with application tools.
        all_tools = list(application_tools)

        # Add long-term memory tools once.
        #
        # The tools are scoped to this user.
        if (
            memory_store is not None
            and user_id is not None
        ):
            memory_tools = create_memory_tools(
                memory_store,
                user_id=user_id,
            )

            existing_names = {
                tool.name
                for tool in all_tools
            }

            for tool in memory_tools:
                if tool.name in existing_names:
                    raise ValueError(
                        "Memory tool name conflicts "
                        f"with existing tool: {tool.name}"
                    )

            all_tools.extend(memory_tools)

        self._tools = {
            tool.name: tool
            for tool in all_tools
        }

        # Bind tools ONCE.
        #
        # This model is reused by every agent node
        # execution for this agent instance.
        self._model = model.bind_tools(
            all_tools
        )

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

        self._checkpointer = InMemorySaver()

        self._graph = builder.compile(
            checkpointer=self._checkpointer,
        )

    def run(
        self,
        question: str,
        *,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        if (
            not isinstance(thread_id, str)
            or not thread_id.strip()
        ):
            raise ValueError(
                "thread_id must be a non-empty string"
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
            initial_state,
            config={
                "configurable": {
                    "thread_id": thread_id,
                }
            },
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

    def _agent_node(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        next_iteration = (
            state["iterations"] + 1
        )

        if (
            next_iteration
            > self._max_iterations
        ):
            raise RuntimeError(
                "LangGraph agent reached "
                "max_iterations without "
                "producing a final answer"
            )


        messages = state["messages"]

        if (self._memory_store is not None and self._user_id is not None):
            messages = [
                SystemMessage(
                    content=MEMORY_BEHAVIOR_PROMPT
                ),
                *messages,
            ]

        response = self._model.invoke(
            messages
        )

        if not isinstance(
            response,
            AIMessage,
        ):
            raise TypeError(
                "The model must return an AIMessage"
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

    def _tool_node(
        self,
        state: AgentState,
    ) -> dict[str, Any]:
        last_message = state["messages"][-1]

        if not isinstance(
            last_message,
            AIMessage,
        ):
            raise TypeError(
                "Tool node expected an AIMessage"
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
                    "Model requested an "
                    f"unregistered tool: {tool_name}"
                )

            try:
                result = tool.invoke(
                    tool_call["args"]
                )
            except Exception:
                tool_messages.append(
                    ToolMessage(
                        content=(
                            "Tool execution failed."
                        ),
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
    def _should_continue(
        state: AgentState,
    ) -> str:
        last_message = state["messages"][-1]

        if not isinstance(
            last_message,
            AIMessage,
        ):
            raise TypeError(
                "Routing expected an AIMessage"
            )

        if last_message.tool_calls:
            return "tools"

        return "end"


def _message_text(
    message: AIMessage,
) -> str:
    content = message.content

    if isinstance(
        content,
        str,
    ):
        return content.strip()

    return str(content).strip()