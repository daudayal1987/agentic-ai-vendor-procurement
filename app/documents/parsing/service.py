from uuid import UUID

from app.documents.repository import DocumentRepository
from app.documents.parsing.factory import DocumentParserFactory
from app.documents.parsing.interface import ParsedDocument
from app.storage.interface import ObjectStorage


class DocumentParsingService:
    def __init__(
        self,
        repository: DocumentRepository,
        storage: ObjectStorage,
        parser_factory: DocumentParserFactory,
    ):
        self.repository = repository
        self.storage = storage
        self.parser_factory = parser_factory

    def parse_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
    ) -> ParsedDocument:

        document = self.repository.get_by_id(
            tenant_id=tenant_id,
            document_id=document_id,
        )

        if document is None:
            raise FileNotFoundError(
                f"Document not found: {document_id}"
            )

        content = self.storage.download(
            document.object_key
        )

        parser = self.parser_factory.get_parser(
            document.content_type
        )

        return parser.parse(
            document_id=document.id,
            content=content,
            content_type=document.content_type,
        )