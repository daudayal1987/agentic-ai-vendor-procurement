from io import BytesIO
from uuid import uuid4

from docx import Document

from app.documents.parsing.docx import DOCXDocumentParser


def test_docx_parser():
    document = Document()
    document.add_paragraph(
        "Vendor shall maintain the SLA."
    )

    buffer = BytesIO()
    document.save(buffer)

    document_id = uuid4()

    parser = DOCXDocumentParser()

    result = parser.parse(
        document_id=document_id,
        content=buffer.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    )

    assert result.document_id == document_id
    assert "Vendor shall maintain the SLA." in result.text