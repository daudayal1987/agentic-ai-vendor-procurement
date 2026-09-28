from uuid import uuid4

import pytest

from app.documents.parsing.text import (
    TextDocumentParser,
)


def test_text_document_parser():

    document_id = uuid4()

    result = TextDocumentParser().parse(
        document_id=document_id,
        content=b"Hello enterprise document.",
        content_type="text/plain",
    )

    assert (
        result.document_id
        == document_id
    )

    assert (
        result.text
        == "Hello enterprise document."
    )

    assert (
        result.content_type
        == "text/plain"
    )

    assert len(result.segments) == 1

    assert (
        result.segments[0].metadata
        == {"source_type": "text"}
    )


def test_empty_text_document():

    result = TextDocumentParser().parse(
        document_id=uuid4(),
        content=b"",
        content_type="text/plain",
    )

    assert result.text == ""

    assert result.segments[0].text == ""


def test_invalid_utf8_fails():

    parser = TextDocumentParser()

    with pytest.raises(
        UnicodeDecodeError
    ):
        parser.parse(
            document_id=uuid4(),
            content=b"\xff\xfe\xfd",
            content_type="text/plain",
        )