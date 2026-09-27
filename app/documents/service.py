from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.storage.interface import ObjectStorage

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}

class DocumentService:
    def __init__(
        self,
        session: Session,
        storage: ObjectStorage,
    ):
        self.session = session
        self.repository = DocumentRepository(session)
        self.storage = storage

    def get_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
    ) -> Document | None:
        return self.repository.get_by_id(
            tenant_id=tenant_id,
            document_id=document_id,
        )

    def list_documents(
        self,
        tenant_id: UUID,
    ) -> list[Document]:
        return self.repository.list_by_tenant(
            tenant_id=tenant_id,
        )

    def upload_document(
        self,
        tenant_id: UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Document:

        extension = Path(filename).suffix.lower()

        expected_content_type = ALLOWED_EXTENSIONS.get(extension)

        if expected_content_type is None:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        if content_type != expected_content_type:
            raise ValueError(
                "File content type does not match file extension"
            )

        document_id = uuid4()
        safe_filename = self._safe_filename(filename)

        object_key = (
            f"documents/{tenant_id}/{document_id}/{filename}"
        )

        self.storage.upload(
            object_key=object_key,
            content=BytesIO(content),
            content_type=content_type,
        )

        document = Document(
            id=document_id,
            tenant_id=tenant_id,
            filename=filename,
            object_key=object_key,
            content_type=content_type,
            size_bytes=len(content),
            status="uploaded",
        )

        try:
            self.repository.create(document)
            self.session.commit()

        except Exception:
            self.session.rollback()

            # Compensating action:
            # remove the object if DB persistence fails.
            self.storage.delete(object_key)

            raise

        return document

    def _safe_filename(filename: str) -> str:
        name = Path(filename).name

        if not name:
            raise ValueError("Invalid filename")

        return name