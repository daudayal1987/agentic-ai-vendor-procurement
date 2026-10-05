from uuid import UUID

import pytest

from app.retrieval.dense import DenseRetriever
from app.retrieval.embeddings.interface import EmbeddingModel
from app.retrieval.vector_store.faiss_index import FaissVectorIndex
from app.retrieval.vector_store.models import IndexedChunk


TENANT_A = UUID(
    "11111111-1111-1111-1111-111111111111"
)


class EvaluationEmbeddingModel(EmbeddingModel):
    @property
    def dimension(self) -> int:
        return 3

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        mapping = {
            "termination_001": [1.0, 0.0, 0.0],
            "security_001": [0.0, 1.0, 0.0],
            "sla_001": [0.0, 0.0, 1.0],
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


@pytest.fixture
def evaluation_retriever() -> DenseRetriever:
    embedding_model = EvaluationEmbeddingModel()

    vector_index = FaissVectorIndex(
        dimension=3
    )

    chunks = [
        IndexedChunk(
            vector_id=0,
            chunk_id=UUID(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
            ),
            document_id=UUID(
                "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"
            ),
            tenant_id=TENANT_A,
            text="termination_001",
            section="Termination",
            position=0,
            token_count=1,
            source_metadata={
                "evaluation_id": "termination_001"
            },
        ),
        IndexedChunk(
            vector_id=1,
            chunk_id=UUID(
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
            ),
            document_id=UUID(
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1"
            ),
            tenant_id=TENANT_A,
            text="security_001",
            section="Security",
            position=0,
            token_count=1,
            source_metadata={
                "evaluation_id": "security_001"
            },
        ),
        IndexedChunk(
            vector_id=2,
            chunk_id=UUID(
                "cccccccc-cccc-cccc-cccc-cccccccccccc"
            ),
            document_id=UUID(
                "cccccccc-cccc-cccc-cccc-ccccccccccc1"
            ),
            tenant_id=TENANT_A,
            text="sla_001",
            section="SLA",
            position=0,
            token_count=1,
            source_metadata={
                "evaluation_id": "sla_001"
            },
        ),
    ]

    vector_index.add(
        embedding_model.embed_documents(
            [
                chunk.text
                for chunk in chunks
            ]
        )
    )

    return DenseRetriever(
        embedding_model=embedding_model,
        vector_index=vector_index,
        indexed_chunks=chunks,
    )