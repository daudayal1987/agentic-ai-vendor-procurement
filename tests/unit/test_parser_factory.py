import pytest

from app.documents.parsing.factory import DocumentParserFactory


def test_parser_factory():
    factory = DocumentParserFactory()

    assert factory.get_parser(
        "application/pdf"
    ).__class__.__name__ == "PDFDocumentParser"

    assert factory.get_parser(
        "text/plain"
    ).__class__.__name__ == "TextDocumentParser"

    assert factory.get_parser(
        "text/markdown"
    ).__class__.__name__ == "MarkdownDocumentParser"


def test_parser_factory_rejects_unknown_type():
    factory = DocumentParserFactory()

    with pytest.raises(ValueError):
        factory.get_parser("application/zip")