from uuid import UUID

from langgraph.types import Command

from app.approvals.service import ApprovalAuthorizationService


class ApprovalResumeService:
    def __init__(
        self,
        approval_service: ApprovalAuthorizationService,
        graph,
    ) -> None:
        self._approval_service = approval_service
        self._graph = graph

    def resume(
        self,
        *,
        approval_id: UUID,
        approver_id: UUID,
        approved: bool,
    ):
        approval = self._approval_service.get_pending_approval(
            approval_id
        )

        if approval is None:
            raise ValueError(
                "Approval does not exist or is no longer pending"
            )

        decision = self._approval_service.record_decision(
            approval_id=approval_id,
            approver_id=approver_id,
            approved=approved,
        )

        if decision is None:
            raise PermissionError(
                "User is not authorized to make this approval decision"
            )

        return self._graph.invoke(
            Command(
                resume={
                    "approver_id": str(approver_id),
                    "approved": approved,
                }
            ),
            config={
                "configurable": {
                    "thread_id": approval.thread_id,
                }
            },
        )