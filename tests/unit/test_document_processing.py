from uuid import uuid4

from app.documents.parsing.interface import (
    ParsedDocument,
    ParsedSegment,
)
from app.documents.processing.chunking import (
    ChunkingConfig,
    SemanticChunker,
)
from app.documents.processing.service import (
    DocumentProcessingService,
)
from app.documents.processing.structure import (
    DocumentStructureDetector,
)


def create_service() -> DocumentProcessingService:

    return DocumentProcessingService(
        structure_detector=(
            DocumentStructureDetector()
        ),
        chunker=SemanticChunker(
            ChunkingConfig(
                target_chunk_size=20,
                min_chunk_size=5,
                max_chunk_size=30,
                chunk_overlap=0,
            )
        ),
    )


def test_document_processing_pipeline():

    document_id = uuid4()
    tenant_id = uuid4()

    parsed = ParsedDocument(
        document_id=document_id,
        content_type="text/plain",
        text=(
            "1. Payment Terms\n\n"
            "Vendor shall submit invoices "
            "within 15 days. "
            "Payment shall be made within "
            "30 days."
        ),
        segments=(
            ParsedSegment(
                text=(
                    "1. Payment Terms\n\n"
                    "Vendor shall submit invoices "
                    "within 15 days. "
                    "Payment shall be made within "
                    "30 days."
                ),
                metadata={
                    "source_type": "text"
                },
            ),
        ),
    )

    result = create_service().process(
        parsed_document=parsed,
        tenant_id=tenant_id,
    )

    assert (
        result.document_id
        == document_id
    )

    assert (
        result.tenant_id
        == tenant_id
    )

    assert result.text.startswith(
        "1. Payment Terms"
    )

    assert len(result.chunks) >= 1

    assert (
        result.statistics.chunk_count
        == len(result.chunks)
    )

    assert (
        result.statistics.total_tokens
        > 0
    )

    assert (
        result.chunks[0].section
        == "1. Payment Terms"
    )

    assert (
        result.chunks[0].source_metadata
        == {
            "sources": (
                {"source_type": "text"},
            )
        }
    )


def test_source_metadata_survives_end_to_end_processing():

    parsed = ParsedDocument(
        document_id=uuid4(),
        content_type="application/pdf",
        text=(
            "Payment Terms\n\n"
            "Payment is due within 30 days."
        ),
        segments=(
            ParsedSegment(
                text=(
                    "Payment Terms\n\n"
                    "Payment is due within 30 days."
                ),
                metadata={
                    "page": 7
                },
            ),
        ),
    )

    result = create_service().process(
        parsed_document=parsed,
        tenant_id=uuid4(),
    )

    assert (
        result.chunks[0].source_metadata
        == {
            "sources": (
                {"page": 7},
            )
        }
    )


def test_empty_document_processing():

    parsed = ParsedDocument(
        document_id=uuid4(),
        content_type="text/plain",
        text="",
    )

    result = create_service().process(
        parsed_document=parsed,
        tenant_id=uuid4(),
    )

    assert result.text == ""
    assert result.chunks == ()

    assert (
        result.statistics.chunk_count
        == 0
    )