from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.db.session import get_db
from app.documents.service import DocumentService
from app.storage.factory import get_object_storage
from app.storage.interface import ObjectStorage


def get_document_service(
    session: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
) -> DocumentService:
    return DocumentService(
        session=session,
        storage=storage,
    )