from __future__ import annotations

from abc import ABC, abstractmethod


class SpecialistAgent(ABC):
    """
    Base boundary for a specialized agent.

    The supervisor only depends on this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's stable name."""

    @abstractmethod
    def run(self, question: str) -> str:
        """Handle a question and return a result."""