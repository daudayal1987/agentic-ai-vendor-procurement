from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.supervisor.router import (
    AgentRoute,
    SupervisorRouter,
)

from app.agents.specialists import (
    ContractAgent,
    PolicyAgent,
    SecurityAgent,
)


class SupervisorState(TypedDict):
    """State carried through the supervisor workflow."""

    question: str
    route: AgentRoute | None
    events: Annotated[list[dict[str, Any]], add,]
    result: str | None


class SupervisorAgent:
    """
    Simple LangGraph supervisor.

    The supervisor:
        1. receives a user question,
        2. determines the required specialist,
        3. routes execution to that specialist node.

    Specialist nodes are placeholders for Day 21.
    """

    def __init__(
        self,
        router: SupervisorRouter | None = None,
        *,
        contract_agent: ContractAgent | None = None,
        security_agent: SecurityAgent | None = None,
        policy_agent: PolicyAgent | None = None,
    ) -> None:
        self._router = router or SupervisorRouter()

        self._contract_agent = (
            contract_agent or ContractAgent()
        )

        self._security_agent = (
            security_agent or SecurityAgent()
        )

        self._policy_agent = (
            policy_agent or PolicyAgent()
        )

        builder = StateGraph(SupervisorState)

        builder.add_node(
            "supervisor",
            self._supervisor_node,
        )

        builder.add_node(
            "contract",
            self._contract_node,
        )

        builder.add_node(
            "security",
            self._security_node,
        )

        builder.add_node(
            "policy",
            self._policy_node,
        )

        builder.add_edge(
            START,
            "supervisor",
        )

        builder.add_conditional_edges(
            "supervisor",
            self._route,
            {
                "contract": "contract",
                "security": "security",
                "policy": "policy",
            },
        )

        builder.add_edge(
            "contract",
            END,
        )

        builder.add_edge(
            "security",
            END,
        )

        builder.add_edge(
            "policy",
            END,
        )

        self._graph = builder.compile()

    def run(
        self,
        question: str,
    ) -> dict[str, Any]:
        """
        Run the supervisor workflow.
        """

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        initial_state: SupervisorState = {
            "question": question.strip(),
            "route": None,
            "events": [],
            "result": None,
        }

        result = self._graph.invoke(
            initial_state
        )

        return {
            "route": result["route"],
            "result": result["result"],
            "events": tuple(result["events"]),
        }

    def _supervisor_node(
        self,
        state: SupervisorState,
    ) -> dict[str, Any]:
        route = self._router.route(
            state["question"]
        )

        events = list(
            state["events"]
        )

        events.append(
            {
                "event_type": "supervisor_route",
                "route": route,
            }
        )

        return {
            "route": route,
            "events": events,
        }

    @staticmethod
    def _route(
        state: SupervisorState,
    ) -> AgentRoute:
        route = state["route"]

        if route is None:
            raise RuntimeError(
                "Supervisor did not produce a route"
            )

        return route


    def _contract_node(
        self,
        state: SupervisorState,
    ) -> dict[str, Any]:
        result = self._contract_agent.run(
            state["question"]
        )

        return {
            "result": result,
            "events": [
                {
                    "event_type": "agent_selected",
                    "agent": self._contract_agent.name,
                }
            ],
        }

    def _security_node(
        self,
        state: SupervisorState,
    ) -> dict[str, Any]:
        result = self._security_agent.run(
            state["question"]
        )

        return {
            "result": result,
            "events": [
                {
                    "event_type": "agent_selected",
                    "agent": self._security_agent.name,
                }
            ],
        }

    def _policy_node(
        self,
        state: SupervisorState,
    ) -> dict[str, Any]:
        result = self._policy_agent.run(
            state["question"]
        )

        return {
            "result": result,
            "events": [
                {
                    "event_type": "agent_selected",
                    "agent": self._policy_agent.name,
                }
            ],
        }