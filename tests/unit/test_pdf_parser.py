import pymupdf
from uuid import uuid4

from app.documents.parsing.pdf import PDFDocumentParser


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

    parser = PDFDocumentParser()

    result = parser.parse(
        document_id=document_id,
        content=content,
        content_type="application/pdf",
    )

    assert result.document_id == document_id
    assert "Vendor shall maintain the SLA." in result.text

def test_empty_pdf():
    document = pymupdf.open()
    document.new_page() 
    content = document.tobytes()
    document.close()

    parser = PDFDocumentParser()

    result = parser.parse(
        document_id=uuid4(),
        content=content,
        content_type="application/pdf",
    )

    assert result.text == ""