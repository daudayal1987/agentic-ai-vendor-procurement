import pytest
from uuid import uuid4

from app.documents.processing.chunking import (
    DocumentChunk,
)
from app.documents.processing.validation import (
    validate_chunks,
)


def make_chunk(
    position: int,
    *,
    chunk_id=None,
    text="chunk",
    token_count=1,
):

    return DocumentChunk(
        chunk_id=(
            chunk_id
            or uuid4()
        ),
        document_id=uuid4(),
        tenant_id=uuid4(),
        text=text,
        section=None,
        position=position,
        token_count=token_count,
    )


def test_valid_chunks():

    chunks = (
        make_chunk(
            0,
            text="First chunk",
            token_count=2,
        ),
        make_chunk(
            1,
            text="Second chunk",
            token_count=2,
        ),
    )

    validate_chunks(chunks)


def test_empty_chunk_is_rejected():

    with pytest.raises(
        ValueError,
        match="empty text",
    ):
        validate_chunks(
            (
                make_chunk(
                    0,
                    text="",
                    token_count=0,
                ),
            )
        )


def test_duplicate_chunk_id_is_rejected():

    chunk_id = uuid4()

    chunks = (
        make_chunk(
            0,
            chunk_id=chunk_id,
        ),
        make_chunk(
            1,
            chunk_id=chunk_id,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Duplicate chunk ID",
    ):
        validate_chunks(chunks)


def test_invalid_position_is_rejected():

    with pytest.raises(
        ValueError,
        match="Invalid chunk position",
    ):
        validate_chunks(
            (
                make_chunk(0),
                make_chunk(2),
            )
        )


def test_invalid_token_count_is_rejected():

    with pytest.raises(
        ValueError,
        match="Invalid token count",
    ):
        validate_chunks(
            (
                make_chunk(
                    0,
                    token_count=0,
                ),
            )
        )