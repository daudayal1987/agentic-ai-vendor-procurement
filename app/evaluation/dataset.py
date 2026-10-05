import json
from pathlib import Path

from app.evaluation.models import RetrievalEvaluationCase


def load_golden_dataset(
    path: Path,
    retrieval_queries: dict[str, str],
) -> list[RetrievalEvaluationCase]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        records = json.load(file)

    cases: list[RetrievalEvaluationCase] = []

    for record in records:
        query_id = record["id"]

        if query_id not in retrieval_queries:
            raise ValueError(
                f"Missing retrieval query for {query_id}"
            )

        cases.append(
            RetrievalEvaluationCase(
                query_id=query_id,
                query=record["query"],
                retrieval_query=retrieval_queries[
                    query_id
                ],
                relevant_chunk_ids=set(
                    record["relevant_chunk_ids"]
                ),
            )
        )

    return cases