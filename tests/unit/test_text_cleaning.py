from app.documents.processing.cleaning import (
    normalize_text,
)


def test_normalize_line_endings():
    text = (
        "Line 1\r\n"
        "Line 2\r"
        "Line 3"
    )

    result = normalize_text(text)

    assert result == (
        "Line 1\n"
        "Line 2\n"
        "Line 3"
    )


def test_remove_trailing_whitespace():
    text = (
        "Line 1   \n"
        "Line 2\t\n"
        "Line 3"
    )

    result = normalize_text(text)

    assert result == (
        "Line 1\n"
        "Line 2\n"
        "Line 3"
    )


def test_collapse_excessive_blank_lines():
    text = (
        "Section 1\n"
        "\n"
        "\n"
        "\n"
        "Payment Terms"
    )

    result = normalize_text(text)

    assert result == (
        "Section 1\n\n"
        "Payment Terms"
    )


def test_strip_document_boundaries():
    text = (
        "\n\n"
        "  Document content  "
        "\n\n"
    )

    result = normalize_text(text)

    assert result == "Document content"


def test_empty_text():
    assert normalize_text("") == ""


def test_preserve_internal_structure():
    text = (
        "Section 1\n\n"
        "Payment Terms\n"
        "Vendor shall pay within 30 days."
    )

    result = normalize_text(text)

    assert result == text