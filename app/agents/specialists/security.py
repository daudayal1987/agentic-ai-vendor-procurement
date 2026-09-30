from __future__ import annotations

from app.agents.specialists.base import SpecialistAgent


class SecurityAgent(SpecialistAgent):
    """Specialist responsible for security-related requests."""

    @property
    def name(self) -> str:
        return "security"

    def run(self, question: str) -> str:
        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        return "security_agent"