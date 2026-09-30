from __future__ import annotations

from app.agents.specialists.base import SpecialistAgent


class ContractAgent(SpecialistAgent):
    """Specialist responsible for contract-related requests."""

    @property
    def name(self) -> str:
        return "contract"

    def run(self, question: str) -> str:
        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                "question must be a non-empty string"
            )

        return "contract_agent"