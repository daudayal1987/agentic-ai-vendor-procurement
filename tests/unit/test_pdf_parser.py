import pymupdf
from uuid import uuid4

from app.documents.parsing.pdf import (
    PDFDocumentParser,
)


def test_pdf_parser():

    document = pymupdf.open()

    page = document.new_page()

    page.insert_text(
        (72, 72),
        "Vendor shall maintain the SLA.",
    )

    content = document.tobytes()

    document.close()

    document_id = uuid4()

    result = PDFDocumentParser().parse(
        document_id=document_id,
        content=content,
        content_type="application/pdf",
    )

    assert (
        result.document_id
        == document_id
    )

    assert (
        "Vendor shall maintain the SLA."
        in result.text
    )

    assert len(result.segments) == 1

    assert (
        result.segments[0].metadata
        == {"page": 1}
    )


def test_pdf_parser_preserves_page_metadata():

    document = pymupdf.open()

    first_page = document.new_page()

    first_page.insert_text(
        (72, 72),
        "First page content.",
    )

    second_page = document.new_page()

    second_page.insert_text(
        (72, 72),
        "Second page content.",
    )

    content = document.tobytes()

    document.close()

    result = PDFDocumentParser().parse(
        document_id=uuid4(),
        content=content,
        content_type="application/pdf",
    )

    assert [
        segment.metadata["page"]
        for segment in result.segments
    ] == [1, 2]


def test_empty_pdf():

    document = pymupdf.open()

    document.new_page()

    content = document.tobytes()

    document.close()

    result = PDFDocumentParser().parse(
        document_id=uuid4(),
        content=content,
        content_type="application/pdf",
    )

    assert result.text == ""
    assert result.segments == ()