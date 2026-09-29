from __future__ import annotations

from functools import lru_cache

from app.common.config import get_settings
from app.retrieval.embeddings.interface import EmbeddingModel
from app.retrieval.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddingModel,
)


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    """
    Return the cached application embedding model.

    Model loading is intentionally cached because loading a local
    Sentence Transformer model for every request would be expensive.
    """

    settings = get_settings()

    return SentenceTransformerEmbeddingModel(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
    )