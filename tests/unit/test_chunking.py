from uuid import uuid4

from app.documents.processing.chunking import (
    ChunkingConfig,
    DocumentChunk,
    SemanticChunker,
    estimate_token_count,
    generate_chunk_id,
)
from app.documents.processing.structure import (
    BlockType,
    DocumentBlock,
    StructuredDocument,
)


def make_block(
    block_type: BlockType,
    text: str,
    position: int,
    source_metadata: dict | None = None,
) -> DocumentBlock:

    return DocumentBlock(
        block_type=block_type,
        text=text,
        position=position,
        source_metadata=(
            source_metadata or {}
        ),
    )


def test_token_estimation():
    assert (
        estimate_token_count(
            "one two three"
        )
        == 3
    )


def test_deterministic_chunk_id():
    document_id = uuid4()

    first = generate_chunk_id(
        document_id,
        0,
    )

    second = generate_chunk_id(
        document_id,
        0,
    )

    assert first == second


def test_different_positions_produce_different_ids():
    document_id = uuid4()

    first = generate_chunk_id(
        document_id,
        0,
    )

    second = generate_chunk_id(
        document_id,
        1,
    )

    assert first != second


def test_heading_context_is_preserved():
    document_id = uuid4()
    tenant_id = uuid4()

    document = StructuredDocument(
        blocks=(
            make_block(
                BlockType.HEADING,
                "Payment Terms",
                0,
            ),
            make_block(
                BlockType.PARAGRAPH,
                (
                    "Vendor shall submit "
                    "invoices within 15 days."
                ),
                1,
            ),
        )
    )

    chunks = SemanticChunker().chunk(
        document=document,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert len(chunks) == 1

    assert (
        chunks[0].section
        == "Payment Terms"
    )

    assert (
        "Payment Terms"
        in chunks[0].text
    )

    assert (
        "Vendor shall submit"
        in chunks[0].text
    )


def test_chunks_are_tenant_and_document_scoped():
    document_id = uuid4()
    tenant_id = uuid4()

    document = StructuredDocument(
        blocks=(
            make_block(
                BlockType.PARAGRAPH,
                "Vendor payment terms.",
                0,
            ),
        )
    )

    chunks = SemanticChunker().chunk(
        document=document,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert (
        chunks[0].document_id
        == document_id
    )

    assert (
        chunks[0].tenant_id
        == tenant_id
    )


def test_chunking_respects_max_size():
    document_id = uuid4()
    tenant_id = uuid4()

    document = StructuredDocument(
        blocks=tuple(
            make_block(
                BlockType.PARAGRAPH,
                "word " * 100,
                i,
            )
            for i in range(5)
        )
    )

    config = ChunkingConfig(
        target_chunk_size=200,
        min_chunk_size=50,
        max_chunk_size=250,
        chunk_overlap=0,
    )

    chunks = SemanticChunker(
        config
    ).chunk(
        document=document,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert len(chunks) >= 2

    assert all(
        chunk.token_count <= 250
        for chunk in chunks
    )


def test_empty_document_produces_no_chunks():
    document = StructuredDocument(
        blocks=()
    )

    chunks = SemanticChunker().chunk(
        document=document,
        document_id=uuid4(),
        tenant_id=uuid4(),
    )

    assert chunks == ()


def test_oversized_paragraph_is_split_by_sentences():
    document_id = uuid4()
    tenant_id = uuid4()

    text = (
        "The vendor shall comply "
        "with the agreement. "
        * 40
    )

    document = StructuredDocument(
        blocks=(
            make_block(
                BlockType.PARAGRAPH,
                text,
                0,
            ),
        )
    )

    config = ChunkingConfig(
        target_chunk_size=50,
        min_chunk_size=10,
        max_chunk_size=80,
        chunk_overlap=0,
    )

    chunks = SemanticChunker(
        config
    ).chunk(
        document=document,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert len(chunks) > 1

    assert all(
        chunk.token_count <= 80
        for chunk in chunks
    )


def test_long_sentence_uses_word_boundary_fallback():
    document_id = uuid4()
    tenant_id = uuid4()

    text = " ".join(
        ["contract"] * 120
    )

    document = StructuredDocument(
        blocks=(
            make_block(
                BlockType.PARAGRAPH,
                text,
                0,
            ),
        )
    )

    config = ChunkingConfig(
        target_chunk_size=50,
        min_chunk_size=10,
        max_chunk_size=60,
        chunk_overlap=0,
    )

    chunks = SemanticChunker(
        config
    ).chunk(
        document=document,
        document_id=document_id,
        tenant_id=tenant_id,
    )

    assert len(chunks) > 1

    assert all(
        chunk.token_count <= 60
        for chunk in chunks
    )


def test_source_metadata_is_propagated_to_chunk():
    document = StructuredDocument(
        blocks=(
            make_block(
                BlockType.HEADING,
                "Payment Terms",
                0,
                {"page": 7},
            ),
            make_block(
                BlockType.PARAGRAPH,
                "Payment is due within 30 days.",
                1,
                {"page": 7},
            ),
            make_block(
                BlockType.PARAGRAPH,
                "Late payment may incur penalties.",
                2,
                {"page": 8},
            ),
        )
    )

    chunks = SemanticChunker(
        ChunkingConfig(
            target_chunk_size=100,
            min_chunk_size=1,
            max_chunk_size=150,
            chunk_overlap=0,
        )
    ).chunk(
        document=document,
        document_id=uuid4(),
        tenant_id=uuid4(),
    )

    assert len(chunks) == 1

    assert (
        chunks[0].source_metadata
        == {
            "sources": (
                {"page": 7},
                {"page": 8},
            )
        }
    )


def test_chunking_config_rejects_invalid_ranges():

    invalid_configs = (
        {"min_chunk_size": 0},
        {
            "min_chunk_size": 100,
            "target_chunk_size": 50,
        },
        {
            "target_chunk_size": 300,
            "max_chunk_size": 200,
        },
        {"chunk_overlap": -1},
        {
            "max_chunk_size": 50,
            "chunk_overlap": 50,
        },
    )

    for kwargs in invalid_configs:

        try:
            ChunkingConfig(**kwargs)

        except ValueError:
            continue

        raise AssertionError(
            "Expected invalid config to raise: "
            f"{kwargs}"
        )


def test_document_chunk_defaults_source_metadata():
    chunk = DocumentChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        tenant_id=uuid4(),
        text="content",
        section=None,
        position=0,
        token_count=1,
    )

    assert chunk.source_metadata == {}