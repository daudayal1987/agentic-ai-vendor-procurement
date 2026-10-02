from uuid import UUID

from sqlalchemy.orm import Session

from app.common.db.models import ApprovalAudit


class ApprovalAuditRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        tenant_id: UUID,
        requester_id: UUID,
        approver_id: UUID | None,
        approved: bool,
        status: str,
        thread_id: str,
    ) -> ApprovalAudit:
        audit = ApprovalAudit(
            tenant_id=tenant_id,
            requester_id=requester_id,
            approver_id=approver_id,
            approved=approved,
            status=status,
            thread_id=thread_id,
        )

        self._db.add(audit)
        self._db.commit()
        self._db.refresh(audit)

        return audit

    def get_by_id(
        self,
        approval_id: UUID,
    ) -> ApprovalAudit | None:
        return self._db.get(
            ApprovalAudit,
            approval_id,
        )

    def get_by_thread_id(
        self,
        thread_id: str,
    ) -> ApprovalAudit | None:
        return (
            self._db.query(ApprovalAudit)
            .filter(
                ApprovalAudit.thread_id == thread_id,
            )
            .first()
        )