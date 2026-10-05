from app.evaluation.models import RetrievalEvaluationCase
from app.evaluation.runner import (
    evaluate_retrieval,
    evaluate_retrieval_case,
)


def evaluation_cases() -> list[RetrievalEvaluationCase]:
    return [
        RetrievalEvaluationCase(
            query_id="q001",
            query=(
                "What are the vendor contract "
                "termination conditions?"
            ),
            retrieval_query="termination",
            relevant_chunk_ids={
                "termination_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q002",
            query=(
                "What security requirements "
                "must the vendor satisfy?"
            ),
            retrieval_query="security",
            relevant_chunk_ids={
                "security_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q003",
            query=(
                "What SLA commitments "
                "does the vendor have?"
            ),
            retrieval_query="sla",
            relevant_chunk_ids={
                "sla_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q004",
            query="Which clause describes termination?",
            retrieval_query="termination",
            relevant_chunk_ids={
                "termination_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q005",
            query=(
                "What are the vendor's "
                "security obligations?"
            ),
            retrieval_query="security",
            relevant_chunk_ids={
                "security_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q006",
            query=(
                "What happens if the vendor "
                "fails the SLA?"
            ),
            retrieval_query="sla",
            relevant_chunk_ids={
                "sla_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q007",
            query=(
                "What security and SLA "
                "obligations does the vendor have?"
            ),
            retrieval_query="security",
            relevant_chunk_ids={
                "security_001",
                "sla_001",
            },
        ),
    ]


def test_evaluate_single_case(
    evaluation_retriever,
) -> None:
    case = evaluation_cases()[0]

    result = evaluate_retrieval_case(
        evaluation_retriever,
        case,
        k=3,
    )

    assert result.query_id == "q001"
    assert result.recall_at_k == 1.0
    assert result.hit_rate_at_k == 1.0
    assert result.reciprocal_rank == 1.0
    assert result.ndcg_at_k == 1.0


def test_evaluate_entire_dataset(
    evaluation_retriever,
) -> None:
    summary = evaluate_retrieval(
        evaluation_retriever,
        evaluation_cases(),
        k=3,
    )

    assert summary.query_count == 7

    assert 0.0 <= summary.precision_at_k <= 1.0
    assert 0.0 <= summary.recall_at_k <= 1.0
    assert 0.0 <= summary.hit_rate_at_k <= 1.0
    assert 0.0 <= summary.mrr <= 1.0
    assert 0.0 <= summary.ndcg_at_k <= 1.0