from __future__ import annotations

from app.agents.specialists.base import SpecialistAgent


class PolicyAgent(SpecialistAgent):
    """Specialist responsible for policy-related requests."""

    @property
    def name(self) -> str:
        return "policy"

    def run(self, question: str) -> str:
        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        return "policy_agent"