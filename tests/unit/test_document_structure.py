from app.documents.parsing.interface import (
    ParsedSegment,
)
from app.documents.processing.structure import (
    BlockType,
    DocumentStructureDetector,
)


def test_detect_numbered_headings():
    text = """1. Payment Terms

Vendor shall make payment within 30 days.

2. Termination

Either party may terminate the agreement.
"""

    result = DocumentStructureDetector().detect(
        text
    )

    assert len(result.blocks) == 4

    assert (
        result.blocks[0].block_type
        == BlockType.HEADING
    )

    assert (
        result.blocks[0].text
        == "1. Payment Terms"
    )

    assert (
        result.blocks[1].block_type
        == BlockType.PARAGRAPH
    )

    assert (
        result.blocks[2].block_type
        == BlockType.HEADING
    )

    assert (
        result.blocks[2].text
        == "2. Termination"
    )

    assert (
        result.blocks[3].block_type
        == BlockType.PARAGRAPH
    )


def test_detect_uppercase_heading():
    text = """PAYMENT TERMS

Vendor shall make payment within 30 days.
"""

    result = DocumentStructureDetector().detect(
        text
    )

    assert (
        result.blocks[0].block_type
        == BlockType.HEADING
    )

    assert (
        result.blocks[1].block_type
        == BlockType.PARAGRAPH
    )


def test_multiline_block_is_paragraph():
    text = """This is a paragraph
that continues on another line.
"""

    result = DocumentStructureDetector().detect(
        text
    )

    assert len(result.blocks) == 1

    assert (
        result.blocks[0].block_type
        == BlockType.PARAGRAPH
    )


def test_empty_document():
    result = DocumentStructureDetector().detect(
        ""
    )

    assert result.blocks == ()


def test_positions_are_deterministic():
    text = """1. Terms

First paragraph.

2. Conditions

Second paragraph.
"""

    result = DocumentStructureDetector().detect(
        text
    )

    assert [
        block.position
        for block in result.blocks
    ] == [0, 1, 2, 3]


def test_source_metadata_is_preserved():
    result = DocumentStructureDetector().detect(
        "Payment Terms\n\n"
        "Payment is due within 30 days.",
        source_metadata={"page": 7},
    )

    assert all(
        block.source_metadata == {"page": 7}
        for block in result.blocks
    )


def test_segment_metadata_is_preserved():
    segments = (
        ParsedSegment(
            text=(
                "Payment Terms\n\n"
                "Payment is due within 30 days."
            ),
            metadata={"page": 7},
        ),
        ParsedSegment(
            text=(
                "Termination\n\n"
                "Either party may terminate."
            ),
            metadata={"page": 8},
        ),
    )

    result = (
        DocumentStructureDetector()
        .detect_segments(segments)
    )

    assert (
        result.blocks[0].source_metadata
        == {"page": 7}
    )

    assert (
        result.blocks[1].source_metadata
        == {"page": 7}
    )

    assert (
        result.blocks[2].source_metadata
        == {"page": 8}
    )

    assert (
        result.blocks[3].source_metadata
        == {"page": 8}
    )