from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ParsedDocument:
    document_id: UUID
    text: str
    content_type: str


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
        """Parse document bytes into normalized text."""
        raise NotImplementedError