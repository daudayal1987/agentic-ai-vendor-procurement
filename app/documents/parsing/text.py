from uuid import UUID

from app.documents.parsing.interface import (
    DocumentParser,
    ParsedDocument,
    ParsedSegment,
)


class TextDocumentParser(DocumentParser):

    def supports(self, content_type: str) -> bool:
        return content_type == "text/plain"

    def parse(
        self,
        document_id: UUID,
        content: bytes,
        content_type: str,
    ) -> ParsedDocument:

        text = content.decode("utf-8")

        return ParsedDocument(
            document_id=document_id,
            text=text,
            content_type=content_type,
            segments=(
                ParsedSegment(
                    text=text,
                    metadata={
                        "source_type": "text",
                    },
                ),
            ),
        )