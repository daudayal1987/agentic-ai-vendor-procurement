from uuid import uuid4

from app.documents.parsing.markdown import (
    MarkdownDocumentParser,
)


def test_markdown_parser():

    document_id = uuid4()

    content = (
        b"# Contract\n\n"
        b"Vendor shall comply."
    )

    result = MarkdownDocumentParser().parse(
        document_id=document_id,
        content=content,
        content_type="text/markdown",
    )

    assert (
        result.document_id
        == document_id
    )

    assert (
        result.text
        == "# Contract\n\nVendor shall comply."
    )

    assert len(result.segments) == 1

    assert (
        result.segments[0].metadata
        == {"source_type": "markdown"}
    )