from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ParsedSegment:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDocument:
    document_id: UUID
    text: str
    content_type: str
    segments: tuple[ParsedSegment, ...] = ()


class DocumentParser(ABC):

    @abstractmethod
    def supports(self, content_type: str) -> bool:
        """Return whether this parser supports the content type."""
        raise NotImplementedError

    @abstractmethod
    def parse(
        self,
        document_id: UUID,
        content: bytes,
        content_type: str,
    ) -> ParsedDocument:
        """Parse document bytes into extracted text."""
        raise NotImplementedError