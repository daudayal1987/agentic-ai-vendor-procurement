from uuid import UUID

import pymupdf

from app.documents.parsing.interface import (
    DocumentParser,
    ParsedDocument,
    ParsedSegment,
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

        try:
            segments: list[ParsedSegment] = []

            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text()

                if not page_text.strip():
                    continue

                segments.append(
                    ParsedSegment(
                        text=page_text,
                        metadata={
                            "page": page_number,
                        },
                    )
                )

            return ParsedDocument(
                document_id=document_id,
                text="\n\n".join(
                    segment.text
                    for segment in segments
                ),
                content_type=content_type,
                segments=tuple(segments),
            )

        finally:
            pdf.close()