from collections.abc import Sequence

from app.evaluation.models import (
    RetrievalEvaluationCase,
    RetrievalEvaluationResult,
    RetrievalEvaluationSummary,
)
from app.evaluation.retrieval import (
    hit_rate_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.retrieval.dense import DenseRetriever


def evaluate_retrieval_case(
    retriever: DenseRetriever,
    case: RetrievalEvaluationCase,
    k: int,
) -> RetrievalEvaluationResult:
    results = retriever.retrieve(
        case.retrieval_query,
        top_k=k,
    )

    retrieved_ids = [
        result.source_metadata["evaluation_id"]
        for result in results
    ]

    return RetrievalEvaluationResult(
        query_id=case.query_id,
        precision_at_k=precision_at_k(
            retrieved_ids,
            case.relevant_chunk_ids,
            k,
        ),
        recall_at_k=recall_at_k(
            retrieved_ids,
            case.relevant_chunk_ids,
            k,
        ),
        hit_rate_at_k=hit_rate_at_k(
            retrieved_ids,
            case.relevant_chunk_ids,
            k,
        ),
        reciprocal_rank=reciprocal_rank(
            retrieved_ids,
            case.relevant_chunk_ids,
            k,
        ),
        ndcg_at_k=ndcg_at_k(
            retrieved_ids,
            case.relevant_chunk_ids,
            k,
        ),
    )


def evaluate_retrieval(
    retriever: DenseRetriever,
    cases: Sequence[RetrievalEvaluationCase],
    k: int,
) -> RetrievalEvaluationSummary:
    if not cases:
        raise ValueError(
            "At least one evaluation case is required"
        )

    results = [
        evaluate_retrieval_case(
            retriever,
            case,
            k,
        )
        for case in cases
    ]

    count = len(results)

    return RetrievalEvaluationSummary(
        precision_at_k=(
            sum(
                result.precision_at_k
                for result in results
            )
            / count
        ),
        recall_at_k=(
            sum(
                result.recall_at_k
                for result in results
            )
            / count
        ),
        hit_rate_at_k=(
            sum(
                result.hit_rate_at_k
                for result in results
            )
            / count
        ),
        mrr=(
            sum(
                result.reciprocal_rank
                for result in results
            )
            / count
        ),
        ndcg_at_k=(
            sum(
                result.ndcg_at_k
                for result in results
            )
            / count
        ),
        query_count=count,
    )