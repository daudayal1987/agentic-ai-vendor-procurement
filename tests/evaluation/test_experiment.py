from app.evaluation.models import RetrievalEvaluationCase
from app.evaluation.runner import evaluate_retrieval


class BadRetriever:
    def retrieve(
        self,
        query: str,
        top_k: int,
    ):
        return [
            type(
                "Result",
                (),
                {
                    "source_metadata": {
                        "evaluation_id": "unrelated_001"
                    }
                },
            )()
        ][:top_k]


def test_bad_retriever_has_zero_retrieval_metrics() -> None:
    cases = [
        RetrievalEvaluationCase(
            query_id="q001",
            query="What are the vendor contract termination conditions?",
            retrieval_query="termination",
            relevant_chunk_ids={
                "termination_001",
            },
        ),
        RetrievalEvaluationCase(
            query_id="q002",
            query="What security requirements must the vendor satisfy?",
            retrieval_query="security",
            relevant_chunk_ids={
                "security_001",
            },
        ),
    ]

    summary = evaluate_retrieval(
        BadRetriever(),
        cases,
        k=3,
    )

    assert summary.precision_at_k == 0.0
    assert summary.recall_at_k == 0.0
    assert summary.hit_rate_at_k == 0.0
    assert summary.mrr == 0.0
    assert summary.ndcg_at_k == 0.0