from __future__ import annotations

from typing import Sequence

from sentence_transformers import SentenceTransformer

from app.retrieval.embeddings.interface import EmbeddingModel


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    """
    Sentence Transformers implementation of the application-level
    EmbeddingModel interface.

    The selected Day 11 model is:

        BAAI/bge-small-en-v1.5

    It produces 384-dimensional embeddings.
    """

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
    ) -> None:
        if not model_name.strip():
            raise ValueError(
                "model_name must not be empty"
            )

        self._model = SentenceTransformer(
            model_name,
            device=device,
        )

        dimension = self._model.get_sentence_embedding_dimension()

        if dimension is None:
            raise RuntimeError(
                "Unable to determine embedding dimension"
            )

        self._dimension = int(dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(
        self,
        texts: Sequence[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        if any(
            not isinstance(text, str) or not text.strip()
            for text in texts
        ):
            raise ValueError(
                "All document texts must be non-empty strings"
            )

        embeddings = self._model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                "Query text must be a non-empty string"
            )

        if hasattr(self._model, "encode_query"):
            embedding = self._model.encode_query(
                text,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        else:
            embedding = self._model.encode(
                text,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

        return embedding.tolist()