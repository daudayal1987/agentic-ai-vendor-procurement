from app.documents.parsing.interface import DocumentParser

from app.documents.parsing.docx import DOCXDocumentParser
from app.documents.parsing.markdown import MarkdownDocumentParser
from app.documents.parsing.pdf import PDFDocumentParser
from app.documents.parsing.text import TextDocumentParser


class DocumentParserFactory:

    def __init__(self) -> None:
        self.parsers: list[DocumentParser] = [
            PDFDocumentParser(),
            DOCXDocumentParser(),
            TextDocumentParser(),
            MarkdownDocumentParser(),
        ]

    def get_parser(
        self,
        content_type: str,
    ) -> DocumentParser:

        for parser in self.parsers:
            if parser.supports(content_type):
                return parser

        raise ValueError(
            f"Unsupported document content type: {content_type}"
        )