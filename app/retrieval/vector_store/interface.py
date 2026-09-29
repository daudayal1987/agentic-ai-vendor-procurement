from __future__ import annotations

from abc import ABC, abstractmethod

from app.retrieval.vector_store.models import VectorSearchResult


class VectorIndex(ABC):
    """
    Application-level vector index abstraction.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def add(
        self,
        vectors: list[list[float]],
    ) -> list[int]:
        """
        Add vectors and return their generated vector IDs.
        """
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
    ) -> list[VectorSearchResult]:
        """
        Search for the nearest vectors.
        """
        raise NotImplementedError