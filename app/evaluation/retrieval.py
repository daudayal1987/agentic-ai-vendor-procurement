import math
from collections.abc import Sequence


def precision_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    retrieved = list(retrieved_ids[:k])

    if not retrieved:
        return 0.0

    relevant_retrieved = sum(
        1
        for item in retrieved
        if item in relevant_ids
    )

    return relevant_retrieved / len(retrieved)


def recall_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    if not relevant_ids:
        return 0.0

    retrieved = set(retrieved_ids[:k])

    relevant_retrieved = len(
        retrieved & relevant_ids
    )

    return relevant_retrieved / len(relevant_ids)


def hit_rate_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    retrieved = set(retrieved_ids[:k])

    return float(
        bool(retrieved & relevant_ids)
    )

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


def ndcg_at_k(
    retrieved_ids: Sequence[str],
    relevant_ids: set[str],
    k: int,
) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero")

    if not relevant_ids:
        return 0.0

    retrieved = retrieved_ids[:k]

    dcg = 0.0

    for rank, item in enumerate(retrieved, start=1):
        if item in relevant_ids:
            dcg += 1.0 / math.log2(rank + 1)

    ideal_relevant_count = min(
        len(relevant_ids),
        k,
    )

    idcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )

    if idcg == 0.0:
        return 0.0

    return dcg / idcg