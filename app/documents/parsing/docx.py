from io import BytesIO
from uuid import UUID

from docx import Document

from app.documents.parsing.interface import (
    DocumentParser,
    ParsedDocument,
)


class DOCXDocumentParser(DocumentParser):

    def supports(self, content_type: str) -> bool:
        return content_type == (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )

    def parse(
        self,
        document_id: UUID,
        content: bytes,
        content_type: str,
    ) -> ParsedDocument:

        document = Document(BytesIO(content))

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
        ]

        text = "\n\n".join(paragraphs)

        return ParsedDocument(
            document_id=document_id,
            text=text,
            content_type=content_type,
        )