from __future__ import annotations

from uuid import UUID, uuid4

from app.retrieval.dense import DenseRetriever
from app.retrieval.embeddings.dependencies import get_embedding_model
from app.retrieval.vector_store.faiss_index import FaissVectorIndex
from app.retrieval.vector_store.models import IndexedChunk


TENANT_ID = UUID(
    "11111111-1111-1111-1111-111111111111"
)


def build_demo_chunks() -> list[IndexedChunk]:
    """
    Build a small deterministic corpus for the Day 11 experiment.
    """

    return [
        IndexedChunk(
            vector_id=0,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_ID,
            text=(
                "Termination: Either party may terminate the "
                "agreement with 30 days written notice."
            ),
            section="Termination",
            position=0,
            token_count=12,
            source_metadata={
                "filename": "vendor-contract.pdf",
                "page": 4,
            },
        ),
        IndexedChunk(
            vector_id=1,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_ID,
            text=(
                "Security controls require multi-factor "
                "authentication and quarterly access reviews."
            ),
            section="Security",
            position=0,
            token_count=11,
            source_metadata={
                "filename": "security-questionnaire.pdf",
                "page": 7,
            },
        ),
        IndexedChunk(
            vector_id=2,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_ID,
            text=(
                "The service level agreement requires "
                "99.9% monthly service availability."
            ),
            section="SLA",
            position=0,
            token_count=10,
            source_metadata={
                "filename": "vendor-sla.pdf",
                "page": 2,
            },
        ),
        IndexedChunk(
            vector_id=3,
            chunk_id=uuid4(),
            document_id=uuid4(),
            tenant_id=TENANT_ID,
            text=(
                "Invoices must be submitted within 15 days "
                "after the end of each billing period."
            ),
            section="Payment",
            position=0,
            token_count=13,
            source_metadata={
                "filename": "vendor-contract.pdf",
                "page": 12,
            },
        ),
    ]


def main() -> None:
    embedding_model = get_embedding_model()

    print(
        f"Embedding dimension: "
        f"{embedding_model.dimension}"
    )

    vector_index = FaissVectorIndex(
        dimension=embedding_model.dimension
    )

    chunks = build_demo_chunks()

    embeddings = embedding_model.embed_documents(
        [
            chunk.text
            for chunk in chunks
        ]
    )

    vector_index.add(
        embeddings
    )

    retriever = DenseRetriever(
        embedding_model=embedding_model,
        vector_index=vector_index,
        indexed_chunks=chunks,
    )

    queries = [
        "What is the termination notice period?",
        "What security controls are required?",
        "What is the SLA availability requirement?",
        "How should invoices be submitted?",
    ]

    for query in queries:
        results, metrics = (
            retriever.retrieve_with_metrics(
                query,
                top_k=1,
                tenant_id=TENANT_ID,
            )
        )

        print(
            "\n=============================="
        )
        print(
            f"Query: {query}"
        )

        for result in results:
            print(
                f"Section: {result.section}"
            )
            print(
                f"Score: {result.score:.4f}"
            )
            print(
                f"Text: {result.text}"
            )
            print(
                f"Metadata: {result.source_metadata}"
            )

        print(
            "\nLatency:"
        )
        print(
            f"  Embedding: "
            f"{metrics.embedding_latency_ms:.2f} ms"
        )
        print(
            f"  Search: "
            f"{metrics.search_latency_ms:.2f} ms"
        )
        print(
            f"  Total: "
            f"{metrics.total_latency_ms:.2f} ms"
        )


if __name__ == "__main__":
    main()