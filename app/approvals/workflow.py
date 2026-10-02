from uuid import UUID

from app.approvals.service import ApprovalAuthorizationService


class ApprovalWorkflow:
    def __init__(
        self,
        approval_service: ApprovalAuthorizationService,
    ) -> None:
        self._approval_service = approval_service

    def request_approval(
        self,
        *,
        tenant_id: UUID,
        requester_id: UUID,
        thread_id: str,
    ):
        if not self._approval_service.can_execute(
            tenant_id=tenant_id,
            user_id=requester_id,
        ):
            raise PermissionError(
                "Requester is not authorized to execute this action"
            )

        return self._approval_service.create_approval(
            tenant_id=tenant_id,
            requester_id=requester_id,
            thread_id=thread_id,
        )

    def approve(
        self,
        *,
        approval_id: UUID,
        approver_id: UUID,
    ):
        approval = self._approval_service.record_decision(
            approval_id=approval_id,
            approver_id=approver_id,
            approved=True,
        )

        if approval is None:
            raise PermissionError(
                "Approval cannot be approved by this user"
            )

        return approval

    def reject(
        self,
        *,
        approval_id: UUID,
        approver_id: UUID,
    ):
        approval = self._approval_service.record_decision(
            approval_id=approval_id,
            approver_id=approver_id,
            approved=False,
        )

        if approval is None:
            raise PermissionError(
                "Approval cannot be rejected by this user"
            )

        return approval