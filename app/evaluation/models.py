from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    query_id: str
    query: str
    retrieval_query: str
    relevant_chunk_ids: set[str]


@dataclass(frozen=True)
class RetrievalEvaluationResult:
    query_id: str
    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    reciprocal_rank: float
    ndcg_at_k: float


@dataclass(frozen=True)
class RetrievalEvaluationSummary:
    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    mrr: float
    ndcg_at_k: float
    query_count: int