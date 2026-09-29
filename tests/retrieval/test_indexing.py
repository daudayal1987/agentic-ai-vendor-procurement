from uuid import UUID, uuid4

import pytest

from app.documents.processing.chunking import DocumentChunk
from app.retrieval.embeddings.interface import EmbeddingModel
from app.retrieval.indexing import DocumentChunkIndexer
from app.retrieval.vector_store.faiss_index import FaissVectorIndex


TENANT_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)


class FakeEmbeddingModel(EmbeddingModel):
    @property
    def dimension(self) -> int:
        return 3

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [
            [1.0, 0.0, 0.0]
            for _ in texts
        ]

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        return [1.0, 0.0, 0.0]


def build_chunk(text: str) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        tenant_id=TENANT_ID,
        text=text,
        section="Test",
        position=0,
        token_count=len(text.split()),
        source_metadata={
            "filename": "test.pdf"
        },
    )


def test_index_chunks() -> None:
    model = FakeEmbeddingModel()

    index = FaissVectorIndex(
        dimension=3
    )

    indexer = DocumentChunkIndexer(
        embedding_model=model,
        vector_index=index,
    )

    chunks = [
        build_chunk("first"),
        build_chunk("second"),
    ]

    result = indexer.index_chunks(
        chunks
    )

    assert len(result.indexed_chunks) == 2
    assert index.size == 2

    assert (
        result.indexed_chunks[0].chunk_id
        == chunks[0].chunk_id
    )

    assert (
        result.indexed_chunks[0].tenant_id
        == TENANT_ID
    )


def test_empty_chunks_return_empty_result() -> None:
    model = FakeEmbeddingModel()

    index = FaissVectorIndex(
        dimension=3
    )

    indexer = DocumentChunkIndexer(
        embedding_model=model,
        vector_index=index,
    )

    result = indexer.index_chunks([])

    assert result.indexed_chunks == []
    assert index.size == 0


def test_dimension_mismatch_is_rejected() -> None:
    class FourDimensionModel(
        FakeEmbeddingModel
    ):
        @property
        def dimension(self) -> int:
            return 4

    model = FourDimensionModel()

    index = FaissVectorIndex(
        dimension=3
    )

    with pytest.raises(ValueError):
        DocumentChunkIndexer(
            embedding_model=model,
            vector_index=index,
        )