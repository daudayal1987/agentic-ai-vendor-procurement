from app.retrieval.metrics import RetrievalMetrics


def test_retrieval_metrics() -> None:
    metrics = RetrievalMetrics(
        embedding_latency_ms=10.0,
        search_latency_ms=2.0,
        total_latency_ms=12.0,
        result_count=3,
    )

    assert metrics.embedding_latency_ms == 10.0
    assert metrics.search_latency_ms == 2.0
    assert metrics.total_latency_ms == 12.0
    assert metrics.result_count == 3