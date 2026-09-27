from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.documents.models import Document


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, document: Document) -> Document:
        self.session.add(document)
        self.session.flush()
        return document

    def get_by_id(
        self,
        tenant_id: UUID,
        document_id: UUID,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )

        return self.session.scalar(statement)