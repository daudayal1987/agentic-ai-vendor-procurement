from uuid import UUID, uuid4

import pytest

from app.retrieval.dense import DenseRetriever
from app.retrieval.embeddings.interface import EmbeddingModel
from app.retrieval.models import RetrievedChunk
from app.retrieval.vector_store.faiss_index import FaissVectorIndex
from app.retrieval.vector_store.models import IndexedChunk


TENANT_A = UUID(
    "11111111-1111-1111-1111-111111111111"
)

TENANT_B = UUID(
    "22222222-2222-2222-2222-222222222222"
)


class FakeEmbeddingModel(EmbeddingModel):
    @property
    def dimension(self) -> int:
        return 3

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        mapping = {
            "termination": [1.0, 0.0, 0.0],
            "security": [0.0, 1.0, 0.0],
            "sla": [0.0, 0.0, 1.0],
        }

        return [
            mapping[text]
            for text in texts
        ]

    def embed_query(
        self,
        text: str,
    ) -> list[float]:
        mapping = {
            "termination": [1.0, 0.0, 0.0],
            "security": [0.0, 1.0, 0.0],
            "sla": [0.0, 0.0, 1.0],
        }

        return mapping[text]


def build_retriever() -> DenseRetriever:
    model = FakeEmbeddingModel()

    index = FaissVectorIndex(
        dimension=3
    )

    chunks = [
        IndexedChunk(
            vector_id=0,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_A,
            text="termination",
            section="Termination",
            position=0,
            token_count=1,
            source_metadata={},
        ),
        IndexedChunk(
            vector_id=1,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_A,
            text="security",
            section="Security",
            position=0,
            token_count=1,
            source_metadata={},
        ),
        IndexedChunk(
            vector_id=2,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_B,
            text="sla",
            section="SLA",
            position=0,
            token_count=1,
            source_metadata={},
        ),
    ]

    index.add(
        model.embed_documents(
            [
                chunk.text
                for chunk in chunks
            ]
        )
    )

    return DenseRetriever(
        embedding_model=model,
        vector_index=index,
        indexed_chunks=chunks,
    )


def test_semantic_ranking() -> None:
    retriever = build_retriever()

    results = retriever.retrieve(
        "termination",
        top_k=2,
    )

    assert results
    assert results[0].text == "termination"


def test_metadata_is_preserved() -> None:
    retriever = build_retriever()

    results = retriever.retrieve(
        "security",
        top_k=1,
    )

    assert results[0].section == "Security"


def test_tenant_filtering() -> None:
    retriever = build_retriever()

    results = retriever.retrieve(
        "sla",
        top_k=3,
        tenant_id=TENANT_A,
    )

    assert all(
        result.tenant_id == TENANT_A
        for result in results
    )


def test_other_tenant_is_returned_when_no_filter() -> None:
    retriever = build_retriever()

    results = retriever.retrieve(
        "sla",
        top_k=3,
    )

    assert results
    assert results[0].tenant_id == TENANT_B


def test_empty_query_is_rejected() -> None:
    retriever = build_retriever()

    with pytest.raises(ValueError):
        retriever.retrieve(
            "",
        )


def test_invalid_top_k_is_rejected() -> None:
    retriever = build_retriever()

    with pytest.raises(ValueError):
        retriever.retrieve(
            "security",
            top_k=0,
        )


def test_top_k_above_max_is_rejected() -> None:
    retriever = build_retriever()

    with pytest.raises(ValueError):
        retriever.retrieve(
            "security",
            top_k=21,
        )


def test_missing_vector_mapping_is_ignored() -> None:
    model = FakeEmbeddingModel()

    index = FaissVectorIndex(
        dimension=3
    )

    index.add(
        [[1.0, 0.0, 0.0]]
    )

    retriever = DenseRetriever(
        embedding_model=model,
        vector_index=index,
        indexed_chunks=[],
    )

    results = retriever.retrieve(
        "termination",
        top_k=1,
    )

    assert results == []


def test_metrics_are_returned() -> None:
    retriever = build_retriever()

    results, metrics = (
        retriever.retrieve_with_metrics(
            "termination",
            top_k=1,
        )
    )

    assert len(results) == 1
    assert metrics.result_count == 1
    assert metrics.embedding_latency_ms >= 0
    assert metrics.search_latency_ms >= 0
    assert metrics.total_latency_ms >= 0