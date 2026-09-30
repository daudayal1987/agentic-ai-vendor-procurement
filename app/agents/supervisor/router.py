from __future__ import annotations

from typing import Literal


AgentRoute = Literal[
    "contract",
    "security",
    "policy",
]


class SupervisorRouter:
    """
    Deterministic supervisor router.

    Decides which specialized agent should handle
    a request based on explicit keyword rules.

    This is intentionally not LLM-based yet.
    """

    _ROUTE_KEYWORDS: dict[AgentRoute, tuple[str, ...]] = {
        "contract": (
            "contract",
            "clause",
            "agreement",
            "termination",
            "indemnity",
            "liability",
            "sla",
            "vendor agreement",
        ),
        "security": (
            "security",
            "authentication",
            "authorization",
            "access control",
            "permission",
            "credential",
            "encryption",
            "vulnerability",
        ),
        "policy": (
            "policy",
            "compliance",
            "procedure",
            "standard",
            "guideline",
            "regulation",
        ),
    }

    def route(self, question: str) -> AgentRoute:
        """
        Determine which specialized agent should handle
        the question.

        Raises:
            ValueError: If the question is empty or cannot
                be routed unambiguously.
        """

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        normalized = question.strip().lower()

        matches: list[AgentRoute] = []

        for route, keywords in self._ROUTE_KEYWORDS.items():
            if any(
                keyword in normalized
                for keyword in keywords
            ):
                matches.append(route)

        if not matches:
            raise ValueError(
                "Supervisor could not determine "
                "the required agent"
            )

        if len(matches) > 1:
            raise ValueError(
                "Supervisor found multiple possible "
                "agents: "
                + ", ".join(matches)
            )

        return matches[0]