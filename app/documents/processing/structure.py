from dataclasses import dataclass, field
from enum import StrEnum
import re
from typing import Any

from app.documents.parsing.interface import ParsedSegment
from app.documents.processing.cleaning import normalize_text


_HEADING_PATTERNS = (
    re.compile(
        r"^\d+(?:\.\d+)*[.)]?\s+.+$"
    ),
    re.compile(
        r"^[A-Z][A-Z0-9\s\-:&/]{2,80}$"
    ),
)


class BlockType(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"


@dataclass(frozen=True)
class DocumentBlock:
    block_type: BlockType
    text: str
    position: int
    source_metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class StructuredDocument:
    blocks: tuple[DocumentBlock, ...]


class DocumentStructureDetector:
    """
    Detect simple document structure using
    deterministic heuristics.
    """

    def detect(
        self,
        text: str,
        source_metadata: dict[str, Any] | None = None,
    ) -> StructuredDocument:

        cleaned_text = normalize_text(text)

        if not cleaned_text:
            return StructuredDocument(
                blocks=()
            )

        metadata = source_metadata or {}

        raw_blocks = re.split(
            r"\n\s*\n",
            cleaned_text,
        )

        blocks: list[DocumentBlock] = []

        for raw_block in raw_blocks:
            block = raw_block.strip()

            if not block:
                continue

            block_type = (
                BlockType.HEADING
                if self._is_heading(block)
                else BlockType.PARAGRAPH
            )

            blocks.append(
                DocumentBlock(
                    block_type=block_type,
                    text=block,
                    position=len(blocks),
                    source_metadata=dict(metadata),
                )
            )

        return StructuredDocument(
            blocks=tuple(blocks)
        )

    def detect_segments(
        self,
        segments: tuple[ParsedSegment, ...],
    ) -> StructuredDocument:
        """
        Detect structure while preserving the source
        metadata attached to each parsed segment.
        """

        blocks: list[DocumentBlock] = []

        for segment in segments:
            structured = self.detect(
                text=segment.text,
                source_metadata=segment.metadata,
            )

            for block in structured.blocks:
                blocks.append(
                    DocumentBlock(
                        block_type=block.block_type,
                        text=block.text,
                        position=len(blocks),
                        source_metadata=dict(
                            block.source_metadata
                        ),
                    )
                )

        return StructuredDocument(
            blocks=tuple(blocks)
        )

    def _is_heading(
        self,
        block: str,
    ) -> bool:

        lines = block.splitlines()

        # A heading should normally be one line.
        if len(lines) != 1:
            return False

        text = lines[0].strip()

        return any(
            pattern.fullmatch(text)
            for pattern in _HEADING_PATTERNS
        )