from dataclasses import dataclass
from uuid import UUID

from app.documents.parsing.interface import (
    ParsedDocument,
    ParsedSegment,
)
from app.documents.processing.chunking import (
    DocumentChunk,
    SemanticChunker,
)
from app.documents.processing.cleaning import (
    normalize_text,
)
from app.documents.processing.structure import (
    DocumentStructureDetector,
)
from app.documents.processing.validation import (
    validate_chunks,
)


@dataclass(frozen=True)
class ChunkStatistics:
    chunk_count: int
    total_tokens: int
    average_tokens: float
    minimum_tokens: int
    maximum_tokens: int


@dataclass(frozen=True)
class ProcessedDocument:
    document_id: UUID
    tenant_id: UUID
    text: str
    chunks: tuple[DocumentChunk, ...]
    statistics: ChunkStatistics


def calculate_chunk_statistics(
    chunks: tuple[DocumentChunk, ...],
) -> ChunkStatistics:

    if not chunks:
        return ChunkStatistics(
            chunk_count=0,
            total_tokens=0,
            average_tokens=0.0,
            minimum_tokens=0,
            maximum_tokens=0,
        )

    token_counts = [
        chunk.token_count
        for chunk in chunks
    ]

    total_tokens = sum(
        token_counts
    )

    return ChunkStatistics(
        chunk_count=len(chunks),
        total_tokens=total_tokens,
        average_tokens=(
            total_tokens / len(chunks)
        ),
        minimum_tokens=min(
            token_counts
        ),
        maximum_tokens=max(
            token_counts
        ),
    )


class DocumentProcessingService:
    """
    Orchestrate cleaning, structure detection,
    chunking, validation and statistics.
    """

    def __init__(
        self,
        structure_detector: DocumentStructureDetector,
        chunker: SemanticChunker,
    ):
        self.structure_detector = (
            structure_detector
        )
        self.chunker = chunker

    def process(
        self,
        parsed_document: ParsedDocument,
        tenant_id: UUID,
    ) -> ProcessedDocument:

        if parsed_document.segments:

            cleaned_segment_list: list[
                ParsedSegment
            ] = []

            for segment in (
                parsed_document.segments
            ):

                cleaned_segment_text = (
                    normalize_text(
                        segment.text
                    )
                )

                if not cleaned_segment_text:
                    continue

                cleaned_segment_list.append(
                    ParsedSegment(
                        text=cleaned_segment_text,
                        metadata=dict(
                            segment.metadata
                        ),
                    )
                )

            cleaned_segments = tuple(
                cleaned_segment_list
            )

            cleaned_text = "\n\n".join(
                segment.text
                for segment in cleaned_segments
            )

            structured_document = (
                self.structure_detector
                .detect_segments(
                    cleaned_segments
                )
            )

        else:

            cleaned_text = normalize_text(
                parsed_document.text
            )

            structured_document = (
                self.structure_detector
                .detect(
                    cleaned_text
                )
            )

        chunks = self.chunker.chunk(
            document=structured_document,
            document_id=(
                parsed_document.document_id
            ),
            tenant_id=tenant_id,
        )

        validate_chunks(chunks)

        statistics = (
            calculate_chunk_statistics(
                chunks
            )
        )

        return ProcessedDocument(
            document_id=(
                parsed_document.document_id
            ),
            tenant_id=tenant_id,
            text=cleaned_text,
            chunks=chunks,
            statistics=statistics,
        )