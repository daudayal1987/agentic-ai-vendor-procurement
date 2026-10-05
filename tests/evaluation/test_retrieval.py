from collections.abc import Sequence

import pytest

from app.evaluation.retrieval import (
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    hit_rate_at_k,
    reciprocal_rank,
)


def test_precision_at_k() -> None:
    retrieved = [
        "A",
        "B",
        "C",
        "D",
    ]

    relevant = {
        "A",
        "C",
    }

    assert precision_at_k(
        retrieved,
        relevant,
        k=4,
    ) == 0.5


def test_recall_at_k() -> None:
    retrieved = [
        "A",
        "B",
        "C",
        "D",
    ]

    relevant = {
        "A",
        "C",
    }

    assert recall_at_k(
        retrieved,
        relevant,
        k=4,
    ) == 1.0


def test_precision_respects_k() -> None:
    retrieved = [
        "A",
        "B",
        "C",
        "D",
    ]

    relevant = {
        "A",
        "D",
    }

    assert precision_at_k(
        retrieved,
        relevant,
        k=2,
    ) == 0.5


def test_recall_respects_k() -> None:
    retrieved = [
        "A",
        "B",
        "C",
        "D",
    ]

    relevant = {
        "A",
        "D",
    }

    assert recall_at_k(
        retrieved,
        relevant,
        k=2,
    ) == 0.5


def test_precision_empty_results() -> None:
    assert precision_at_k(
        [],
        {"A"},
        k=5,
    ) == 0.0


def test_recall_empty_results() -> None:
    assert recall_at_k(
        [],
        {"A"},
        k=5,
    ) == 0.0


def test_invalid_k() -> None:
    with pytest.raises(ValueError):
        precision_at_k(
            ["A"],
            {"A"},
            k=0,
        )

    with pytest.raises(ValueError):
        recall_at_k(
            ["A"],
            {"A"},
            k=0,
        )


def test_recall_with_multiple_relevant_documents() -> None:
    retrieved = [
        "security_001",
        "sla_001",
        "unrelated_001",
    ]

    relevant = {
        "security_001",
        "sla_001",
    }

    assert recall_at_k(
        retrieved,
        relevant,
        k=3,
    ) == 1.0


def test_hit_rate_when_relevant_result_exists() -> None:
    retrieved = [
        "A",
        "B",
        "C",
    ]

    relevant = {
        "C",
    }

    assert hit_rate_at_k(
        retrieved,
        relevant,
        k=3,
    ) == 1.0


def test_hit_rate_when_no_relevant_result_exists() -> None:
    retrieved = [
        "A",
        "B",
        "C",
    ]

    relevant = {
        "D",
    }

    assert hit_rate_at_k(
        retrieved,
        relevant,
        k=3,
    ) == 0.0


def test_hit_rate_respects_k() -> None:
    retrieved = [
        "A",
        "B",
        "C",
    ]

    relevant = {
        "C",
    }

    assert hit_rate_at_k(
        retrieved,
        relevant,
        k=2,
    ) == 0.0


def test_hit_rate_empty_results() -> None:
    assert hit_rate_at_k(
        [],
        {"A"},
        k=5,
    ) == 0.0


def test_hit_rate_invalid_k() -> None:
    with pytest.raises(ValueError):
        hit_rate_at_k(
            ["A"],
            {"A"},
            k=0,
        )


def test_metrics_can_evaluate_actual_retriever(
    evaluation_retriever,
) -> None:
    results = evaluation_retriever.retrieve(
        "security",
        top_k=3,
    )

    retrieved_ids = [
        result.source_metadata["evaluation_id"]
        for result in results
    ]

    relevant_ids = {
        "security_001",
    }

    assert precision_at_k(
        retrieved_ids,
        relevant_ids,
        k=3,
    ) == pytest.approx(1 / 3)

    assert recall_at_k(
        retrieved_ids,
        relevant_ids,
        k=3,
    ) == 1.0

    assert hit_rate_at_k(
        retrieved_ids,
        relevant_ids,
        k=3,
    ) == 1.0

def reciprocal_rank(
    retrieved_ids: Sequence[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    for rank, item in enumerate(
        retrieved_ids[:k],
        start=1,
    ):
        if item in relevant_ids:
            return 1.0 / rank

    return 0.0

def test_reciprocal_rank_first_result() -> None:
    retrieved = [
        "A",
        "B",
        "C",
    ]

    relevant = {
        "A",
    }

    assert reciprocal_rank(
        retrieved,
        relevant,
        k=3,
    ) == 1.0


def test_reciprocal_rank_second_result() -> None:
    retrieved = [
        "X",
        "A",
        "C",
    ]

    relevant = {
        "A",
    }

    assert reciprocal_rank(
        retrieved,
        relevant,
        k=3,
    ) == pytest.approx(0.5)


def test_reciprocal_rank_third_result() -> None:
    retrieved = [
        "X",
        "Y",
        "A",
    ]

    relevant = {
        "A",
    }

    assert reciprocal_rank(
        retrieved,
        relevant,
        k=3,
    ) == pytest.approx(1 / 3)


def test_reciprocal_rank_uses_first_relevant_result() -> None:
    retrieved = [
        "A",
        "B",
        "C",
    ]

    relevant = {
        "A",
        "C",
    }

    assert reciprocal_rank(
        retrieved,
        relevant,
        k=3,
    ) == 1.0


def test_reciprocal_rank_when_no_result_is_relevant() -> None:
    retrieved = [
        "X",
        "Y",
        "Z",
    ]

    relevant = {
        "A",
    }

    assert reciprocal_rank(
        retrieved,
        relevant,
        k=3,
    ) == 0.0


def test_reciprocal_rank_respects_k() -> None:
    retrieved = [
        "X",
        "Y",
        "A",
    ]

    relevant = {
        "A",
    }

    assert reciprocal_rank(
        retrieved,
        relevant,
        k=2,
    ) == 0.0


def test_reciprocal_rank_invalid_k() -> None:
    with pytest.raises(ValueError):
        reciprocal_rank(
            ["A"],
            {"A"},
            k=0,
        )

def test_ndcg_perfect_ranking() -> None:
    retrieved = [
        "A",
        "B",
        "C",
    ]

    relevant = {
        "A",
        "B",
    }

    assert ndcg_at_k(
        retrieved,
        relevant,
        k=3,
    ) == pytest.approx(1.0)


def test_ndcg_penalizes_lower_ranked_relevant_results() -> None:
    retrieved = [
        "X",
        "A",
        "B",
    ]

    relevant = {
        "A",
        "B",
    }

    score = ndcg_at_k(
        retrieved,
        relevant,
        k=3,
    )

    assert 0.0 < score < 1.0


def test_ndcg_is_zero_when_no_relevant_results() -> None:
    retrieved = [
        "X",
        "Y",
        "Z",
    ]

    relevant = {
        "A",
        "B",
    }

    assert ndcg_at_k(
        retrieved,
        relevant,
        k=3,
    ) == 0.0


def test_ndcg_respects_k() -> None:
    retrieved = [
        "X",
        "A",
    ]

    relevant = {
        "A",
    }

    assert ndcg_at_k(
        retrieved,
        relevant,
        k=1,
    ) == 0.0


def test_ndcg_with_single_relevant_result_at_rank_one() -> None:
    retrieved = [
        "A",
        "X",
        "Y",
    ]

    relevant = {
        "A",
    }

    assert ndcg_at_k(
        retrieved,
        relevant,
        k=3,
    ) == pytest.approx(1.0)


def test_ndcg_invalid_k() -> None:
    with pytest.raises(ValueError):
        ndcg_at_k(
            ["A"],
            {"A"},
            k=0,
        )


def test_ndcg_empty_relevance_set() -> None:
    assert ndcg_at_k(
        ["A", "B"],
        set(),
        k=2,
    ) == 0.0    