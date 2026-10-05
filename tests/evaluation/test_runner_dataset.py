from pathlib import Path

from app.evaluation.dataset import load_golden_dataset
from app.evaluation.runner import (
    evaluate_retrieval,
    evaluate_retrieval_case,
)


GOLDEN_DATASET = (
    Path(__file__).parents[2]
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


def load_cases():
    return load_golden_dataset(
        GOLDEN_DATASET,
        RETRIEVAL_QUERIES,
    )


def test_load_golden_dataset() -> None:
    cases = load_cases()

    assert len(cases) == 7

    assert cases[0].query_id == "q001"

    assert (
        cases[0].relevant_chunk_ids
        == {"termination_001"}
    )


def test_evaluate_single_case(
    evaluation_retriever,
) -> None:
    case = load_cases()[0]

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
        load_cases(),
        k=3,
    )

    assert summary.query_count == 7

    assert 0.0 <= summary.precision_at_k <= 1.0
    assert 0.0 <= summary.recall_at_k <= 1.0
    assert 0.0 <= summary.hit_rate_at_k <= 1.0
    assert 0.0 <= summary.mrr <= 1.0
    assert 0.0 <= summary.ndcg_at_k <= 1.0