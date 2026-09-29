from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence


class EmbeddingModel(ABC):
    """
    Application-level abstraction for an embedding model.

    Retrieval code depends on this interface rather than directly
    depending on Sentence Transformers or another embedding provider.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        Return the dimensionality of generated embeddings.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        """
        Generate embeddings for document texts.
        """
        raise NotImplementedError

    @abstractmethod
    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        """
        Generate an embedding for a query.
        """
        raise NotImplementedError