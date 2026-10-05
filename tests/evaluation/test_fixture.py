def test_evaluation_retriever_returns_termination_chunk(
    evaluation_retriever,
) -> None:
    print(evaluation_retriever)
    results = evaluation_retriever.retrieve(
        "termination",
        top_k=3,
    )

    assert results
    assert (
        results[0].source_metadata["evaluation_id"]
        == "termination_001"
    )


def test_evaluation_retriever_returns_security_chunk(
    evaluation_retriever,
) -> None:
    results = evaluation_retriever.retrieve(
        "security",
        top_k=3,
    )

    assert results
    assert (
        results[0].source_metadata["evaluation_id"]
        == "security_001"
    )


def test_evaluation_retriever_returns_sla_chunk(
    evaluation_retriever,
) -> None:
    results = evaluation_retriever.retrieve(
        "sla",
        top_k=3,
    )

    assert results
    assert (
        results[0].source_metadata["evaluation_id"]
        == "sla_001"
    )