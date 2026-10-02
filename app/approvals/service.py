from uuid import UUID

from sqlalchemy.orm import Session

from app.approvals.repository import ApprovalAuditRepository
from app.auth.authorization import has_tenant_permission
from app.policies.rbac import Permission


class ApprovalAuthorizationService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = ApprovalAuditRepository(db)

    def create_approval(
        self,
        *,
        tenant_id: UUID,
        requester_id: UUID,
        thread_id: str,
    ):
        return self._repository.create(
            tenant_id=tenant_id,
            requester_id=requester_id,
            approver_id=None,
            approved=False,
            status="pending",
            thread_id=thread_id,
        )

    def can_approve(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        return has_tenant_permission(
            db=self._db,
            tenant_id=tenant_id,
            user_id=user_id,
            permission=Permission.APPROVAL_REVIEW,
        )

    def can_execute(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> bool:
        return has_tenant_permission(
            db=self._db,
            tenant_id=tenant_id,
            user_id=user_id,
            permission=Permission.ANALYSIS_RUN,
        )

    def get_pending_approval(
        self,
        approval_id: UUID,
    ):
        approval = self._repository.get_by_id(approval_id)

        if approval is None:
            return None

        if approval.status != "pending":
            return None

        return approval

    def record_decision(
        self,
        *,
        approval_id: UUID,
        approver_id: UUID,
        approved: bool,
    ):
        approval = self._repository.get_by_id(approval_id)

        if approval is None:
            return None

        if approval.status != "pending":
            return None

        if not self.can_approve(
            tenant_id=approval.tenant_id,
            user_id=approver_id,
        ):
            return None

        approval.approver_id = approver_id
        approval.approved = approved
        approval.status = (
            "approved"
            if approved
            else "rejected"
        )

        self._db.commit()
        self._db.refresh(approval)

        return approval