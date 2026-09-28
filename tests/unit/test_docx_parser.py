from io import BytesIO
from uuid import uuid4

from docx import Document

from app.documents.parsing.docx import (
    DOCXDocumentParser,
)


CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument."
    "wordprocessingml.document"
)


def create_docx(
    *paragraphs: str,
) -> bytes:

    document = Document()

    for paragraph in paragraphs:
        document.add_paragraph(
            paragraph
        )

    buffer = BytesIO()

    document.save(buffer)

    return buffer.getvalue()


def test_docx_parser():

    result = DOCXDocumentParser().parse(
        document_id=uuid4(),
        content=create_docx(
            "Vendor shall maintain the SLA."
        ),
        content_type=CONTENT_TYPE,
    )

    assert (
        "Vendor shall maintain the SLA."
        in result.text
    )

    assert len(result.segments) == 1

    assert (
        result.segments[0].metadata
        == {"paragraph_index": 0}
    )


def test_docx_parser_preserves_paragraph_metadata():

    result = DOCXDocumentParser().parse(
        document_id=uuid4(),
        content=create_docx(
            "First paragraph.",
            "",
            "Second paragraph.",
        ),
        content_type=CONTENT_TYPE,
    )

    assert [
        segment.metadata[
            "paragraph_index"
        ]
        for segment in result.segments
    ] == [0, 2]