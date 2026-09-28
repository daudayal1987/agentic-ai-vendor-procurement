from uuid import UUID

import pymupdf

from app.documents.parsing.interface import (
    DocumentParser,
    ParsedDocument,
)


class PDFDocumentParser(DocumentParser):

    def supports(self, content_type: str) -> bool:
        return content_type == "application/pdf"

    def parse(
        self,
        document_id: UUID,
        content: bytes,
        content_type: str,
    ) -> ParsedDocument:

        pdf = pymupdf.open(
            stream=content,
            filetype="pdf",
        )

        pages: list[str] = []

        try:
            for page in pdf:
                pages.append(page.get_text())
        finally:
            pdf.close()

        text = "\n\n".join(pages)

        return ParsedDocument(
            document_id=document_id,
            text=text,
            content_type=content_type,
        )