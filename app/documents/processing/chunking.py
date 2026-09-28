from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid5

from app.documents.processing.sentence import split_sentences
from app.documents.processing.structure import (
    BlockType,
    DocumentBlock,
    StructuredDocument,
)


CHUNK_NAMESPACE = UUID(
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
)


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: UUID
    document_id: UUID
    tenant_id: UUID
    text: str
    section: str | None
    position: int
    token_count: int
    source_metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class ChunkingConfig:
    target_chunk_size: int = 300
    min_chunk_size: int = 100
    max_chunk_size: int = 500

    # Baseline currently uses zero overlap.
    # This field is retained for the later
    # overlap experiment.
    chunk_overlap: int = 0

    def __post_init__(self) -> None:

        if self.min_chunk_size <= 0:
            raise ValueError(
                "min_chunk_size must be greater than zero"
            )

        if self.target_chunk_size < self.min_chunk_size:
            raise ValueError(
                "target_chunk_size must be greater than "
                "or equal to min_chunk_size"
            )

        if self.max_chunk_size < self.target_chunk_size:
            raise ValueError(
                "max_chunk_size must be greater than "
                "or equal to target_chunk_size"
            )

        if self.chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative"
            )

        if self.chunk_overlap >= self.max_chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than "
                "max_chunk_size"
            )


def generate_chunk_id(
    document_id: UUID,
    position: int,
) -> UUID:
    """
    Generate a deterministic chunk ID.
    """

    return uuid5(
        CHUNK_NAMESPACE,
        f"{document_id}:{position}",
    )


def estimate_token_count(
    text: str,
) -> int:
    """
    Lightweight token estimate.

    This is intentionally NOT a model-specific
    tokenizer count.
    """

    if not text.strip():
        return 0

    return max(
        1,
        len(text.split()),
    )


class SemanticChunker:
    """
    Create deterministic, heading-aware and
    sentence-aware document chunks.
    """

    def __init__(
        self,
        config: ChunkingConfig | None = None,
    ):
        self.config = (
            config
            or ChunkingConfig()
        )

    def chunk(
        self,
        document: StructuredDocument,
        document_id: UUID,
        tenant_id: UUID,
    ) -> tuple[DocumentChunk, ...]:

        chunks: list[DocumentChunk] = []

        current_parts: list[str] = []
        current_tokens = 0
        current_section: str | None = None
        current_sources: list[dict[str, Any]] = []

        def flush() -> None:
            nonlocal current_parts
            nonlocal current_tokens
            nonlocal current_sources

            if not current_parts:
                return

            text = "\n\n".join(
                current_parts
            ).strip()

            position = len(chunks)

            chunks.append(
                DocumentChunk(
                    chunk_id=generate_chunk_id(
                        document_id,
                        position,
                    ),
                    document_id=document_id,
                    tenant_id=tenant_id,
                    text=text,
                    section=current_section,
                    position=position,
                    token_count=estimate_token_count(
                        text
                    ),
                    source_metadata=(
                        self._merge_source_metadata(
                            current_sources
                        )
                    ),
                )
            )

            current_parts = []
            current_tokens = 0
            current_sources = []

        for block in document.blocks:

            if block.block_type == BlockType.HEADING:
                flush()

                current_section = block.text

                current_parts.append(
                    block.text
                )

                current_tokens = (
                    estimate_token_count(
                        block.text
                    )
                )

                self._add_source(
                    current_sources,
                    block.source_metadata,
                )

                continue

            parts = self._prepare_block_parts(
                block
            )

            for part in parts:

                part_tokens = (
                    estimate_token_count(part)
                )

                if (
                    current_tokens > 0
                    and (
                        current_tokens
                        + part_tokens
                        > self.config.max_chunk_size
                    )
                ):
                    flush()

                current_parts.append(part)

                current_tokens += part_tokens

                self._add_source(
                    current_sources,
                    block.source_metadata,
                )

                if (
                    current_tokens
                    >= self.config.target_chunk_size
                ):
                    flush()

        flush()

        return tuple(chunks)

    def _prepare_block_parts(
        self,
        block: DocumentBlock,
    ) -> tuple[str, ...]:

        block_tokens = estimate_token_count(
            block.text
        )

        if (
            block_tokens
            <= self.config.max_chunk_size
        ):
            return (
                block.text.strip(),
            )

        sentences = split_sentences(
            block.text
        )

        if not sentences:
            return self._split_large_sentence(
                block.text
            )

        parts: list[str] = []

        for sentence in sentences:
            parts.extend(
                self._split_large_sentence(
                    sentence
                )
            )

        return tuple(parts)

    def _split_large_sentence(
        self,
        sentence: str,
    ) -> tuple[str, ...]:

        words = sentence.split()

        if (
            len(words)
            <= self.config.max_chunk_size
        ):
            return (
                sentence.strip(),
            )

        parts: list[str] = []

        for start in range(
            0,
            len(words),
            self.config.max_chunk_size,
        ):
            part = " ".join(
                words[
                    start:
                    start
                    + self.config.max_chunk_size
                ]
            )

            if part:
                parts.append(part)

        return tuple(parts)

    @staticmethod
    def _add_source(
        sources: list[dict[str, Any]],
        metadata: dict[str, Any],
    ) -> None:

        if metadata and metadata not in sources:
            sources.append(
                dict(metadata)
            )

    @staticmethod
    def _merge_source_metadata(
        metadata_items: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not metadata_items:
            return {}

        return {
            "sources": tuple(
                dict(metadata)
                for metadata in metadata_items
            )
        }