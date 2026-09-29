from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.documents.processing.chunking import DocumentChunk
from app.retrieval.embeddings.interface import EmbeddingModel
from app.retrieval.vector_store.interface import VectorIndex
from app.retrieval.vector_store.models import IndexedChunk


@dataclass(frozen=True)
class IndexingResult:
    """
    Result of indexing document chunks.
    """

    indexed_chunks: list[IndexedChunk]


class DocumentChunkIndexer:
    """
    Converts DocumentChunk objects into embeddings and stores them
    in the configured vector index.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_index: VectorIndex,
    ) -> None:
        if (
            embedding_model.dimension
            != vector_index.dimension
        ):
            raise ValueError(
                "embedding model dimension and vector index dimension "
                "must match"
            )

        self._embedding_model = embedding_model
        self._vector_index = vector_index

    def index_chunks(
        self,
        chunks: Sequence[DocumentChunk],
    ) -> IndexingResult:
        if not chunks:
            return IndexingResult(
                indexed_chunks=[]
            )

        texts = [
            chunk.text
            for chunk in chunks
        ]

        embeddings = (
            self._embedding_model.embed_documents(
                texts
            )
        )

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "Embedding count does not match chunk count"
            )

        vector_ids = self._vector_index.add(
            embeddings
        )

        if len(vector_ids) != len(chunks):
            raise RuntimeError(
                "Vector ID count does not match chunk count"
            )

        indexed_chunks = [
            IndexedChunk(
                vector_id=vector_id,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                tenant_id=chunk.tenant_id,
                text=chunk.text,
                section=chunk.section,
                position=chunk.position,
                token_count=chunk.token_count,
                source_metadata=dict(
                    chunk.source_metadata
                ),
            )
            for chunk, vector_id in zip(
                chunks,
                vector_ids,
            )
        ]

        return IndexingResult(
            indexed_chunks=indexed_chunks
        )