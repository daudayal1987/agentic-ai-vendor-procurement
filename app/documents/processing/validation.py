from app.documents.processing.chunking import DocumentChunk


def validate_chunks(
    chunks: tuple[DocumentChunk, ...],
) -> None:
    """
    Validate invariants required by downstream
    retrieval components.
    """

    seen_ids: set = set()

    for expected_position, chunk in enumerate(
        chunks
    ):

        if not chunk.text.strip():
            raise ValueError(
                f"Chunk {chunk.chunk_id} "
                "contains empty text."
            )

        if chunk.position != expected_position:
            raise ValueError(
                f"Invalid chunk position for "
                f"{chunk.chunk_id}."
            )

        if chunk.chunk_id in seen_ids:
            raise ValueError(
                f"Duplicate chunk ID: "
                f"{chunk.chunk_id}"
            )

        if chunk.token_count <= 0:
            raise ValueError(
                f"Invalid token count for "
                f"{chunk.chunk_id}."
            )

        if chunk.document_id is None:
            raise ValueError(
                f"Chunk {chunk.chunk_id} "
                "has no document ID."
            )

        if chunk.tenant_id is None:
            raise ValueError(
                f"Chunk {chunk.chunk_id} "
                "has no tenant ID."
            )

        seen_ids.add(
            chunk.chunk_id
        )