from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalConfig:
    """
    Configuration for retrieval operations.

    No arbitrary minimum similarity threshold is applied by default.
    """

    default_top_k: int = 5
    max_top_k: int = 20
    minimum_score: float | None = None

    def __post_init__(self) -> None:
        if self.default_top_k <= 0:
            raise ValueError(
                "default_top_k must be greater than zero"
            )

        if self.max_top_k <= 0:
            raise ValueError(
                "max_top_k must be greater than zero"
            )

        if self.default_top_k > self.max_top_k:
            raise ValueError(
                "default_top_k cannot exceed max_top_k"
            )