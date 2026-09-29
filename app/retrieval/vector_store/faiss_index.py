from __future__ import annotations

import faiss
import numpy as np

from app.retrieval.vector_store.interface import VectorIndex
from app.retrieval.vector_store.models import VectorSearchResult


class FaissVectorIndex(VectorIndex):
    """
    Exact FAISS vector index using IndexFlatIP.

    Embeddings are normalized before insertion/search, so inner
    product behaves like cosine similarity.
    """

    def __init__(
        self,
        dimension: int,
    ) -> None:
        if dimension <= 0:
            raise ValueError(
                "dimension must be greater than zero"
            )

        self._dimension = dimension
        self._index = faiss.IndexFlatIP(
            dimension
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def size(self) -> int:
        return int(self._index.ntotal)

    def add(
        self,
        vectors: list[list[float]],
    ) -> list[int]:
        if not vectors:
            return []

        array = np.asarray(
            vectors,
            dtype=np.float32,
        )

        if array.ndim != 2:
            raise ValueError(
                "vectors must be a 2-dimensional matrix"
            )

        if array.shape[1] != self.dimension:
            raise ValueError(
                "vector dimension does not match index dimension"
            )

        start_id = self.size

        self._index.add(array)

        return list(
            range(
                start_id,
                start_id + len(vectors),
            )
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int,
    ) -> list[VectorSearchResult]:
        if not query_vector:
            raise ValueError(
                "query_vector must not be empty"
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero"
            )

        if self.size == 0:
            return []

        if len(query_vector) != self.dimension:
            raise ValueError(
                "query vector dimension does not match index dimension"
            )

        actual_top_k = min(
            top_k,
            self.size,
        )

        query_array = np.asarray(
            [query_vector],
            dtype=np.float32,
        )

        scores, vector_ids = self._index.search(
            query_array,
            actual_top_k,
        )

        results: list[VectorSearchResult] = []

        for score, vector_id in zip(
            scores[0],
            vector_ids[0],
        ):
            if vector_id < 0:
                continue

            results.append(
                VectorSearchResult(
                    vector_id=int(vector_id),
                    score=float(score),
                )
            )

        return results