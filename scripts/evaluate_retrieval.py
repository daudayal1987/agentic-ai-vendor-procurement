from pathlib import Path

from sqlalchemy import UUID

from app.evaluation.dataset import load_golden_dataset
from app.evaluation.runner import evaluate_retrieval
from tests.evaluation.conftest import (
    EvaluationEmbeddingModel,
    TENANT_A,
)
from app.retrieval.dense import DenseRetriever
from app.retrieval.vector_store.faiss_index import FaissVectorIndex
from app.retrieval.vector_store.models import IndexedChunk


GOLDEN_DATASET = (
    Path(__file__).parents[1]
    / "app"
    / "evaluation"
    / "golden_retrieval.json"
)


RETRIEVAL_QUERIES = {
    "q001": "termination",
    "q002": "security",
    "q003": "sla",
    "q004": "termination",
    "q005": "security",
    "q006": "sla",
    "q007": "security",
}


def build_retriever() -> DenseRetriever:
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
            [chunk.text for chunk in chunks]
        )
    )

    return DenseRetriever(
        embedding_model=embedding_model,
        vector_index=vector_index,
        indexed_chunks=chunks,
    )


def main() -> None:
    cases = load_golden_dataset(
        GOLDEN_DATASET,
        RETRIEVAL_QUERIES,
    )

    summary = evaluate_retrieval(
        build_retriever(),
        cases,
        k=3,
    )

    print()
    print("=== Retrieval Evaluation Baseline ===")
    print(f"Queries:       {summary.query_count}")
    print(
        f"Precision@3:   {summary.precision_at_k:.4f}"
    )
    print(
        f"Recall@3:      {summary.recall_at_k:.4f}"
    )
    print(
        f"Hit Rate@3:    {summary.hit_rate_at_k:.4f}"
    )
    print(
        f"MRR@3:         {summary.mrr:.4f}"
    )
    print(
        f"NDCG@3:        {summary.ndcg_at_k:.4f}"
    )
    print()


if __name__ == "__main__":
    main()