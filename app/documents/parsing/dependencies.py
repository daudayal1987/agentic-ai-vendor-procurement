from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.db.session import get_db
from app.documents.parsing.factory import DocumentParserFactory
from app.documents.parsing.service import DocumentParsingService
from app.documents.repository import DocumentRepository
from app.storage.factory import get_object_storage
from app.storage.interface import ObjectStorage


def get_document_parsing_service(
    session: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
) -> DocumentParsingService:

    repository = DocumentRepository(session)

    return DocumentParsingService(
        repository=repository,
        storage=storage,
        parser_factory=DocumentParserFactory(),
    )