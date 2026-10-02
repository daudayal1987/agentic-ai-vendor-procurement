from uuid import uuid4

import pytest

from app.approvals.service import ApprovalAuthorizationService
from app.approvals.workflow import ApprovalWorkflow
from app.common.db.models import TenantMembership, User
from app.common.db.session import SessionLocal
from app.policies.rbac import Role
from app.tenants.repository import TenantRepository


def create_user(
    db,
    *,
    email: str,
):
    user = User(
        email=email,
        display_name="Test User",
        password_hash="test-password",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_membership(
    db,
    *,
    tenant_id,
    user_id,
    role: Role,
):
    membership = TenantMembership(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role.value,
        status="active",
    )

    db.add(membership)
    db.commit()

    return membership


def create_test_tenant(db):
    repository = TenantRepository(db)

    return repository.create(
        name=f"Approval Workflow Tenant {uuid4()}",
        slug=f"approval-workflow-{uuid4()}",
    )


def test_request_approval_creates_pending_record():
    db = SessionLocal()

    try:
        tenant = create_test_tenant(db)

        requester = create_user(
            db,
            email=f"requester-{uuid4()}@example.com",
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=requester.id,
            role=Role.ANALYST,
        )

        workflow = ApprovalWorkflow(
            ApprovalAuthorizationService(db)
        )

        approval = workflow.request_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{uuid4()}",
        )

        assert approval.status == "pending"
        assert approval.requester_id == requester.id
        assert approval.approver_id is None
        assert approval.approved is False

    finally:
        db.close()


def test_approver_can_approve_pending_request():
    db = SessionLocal()

    try:
        tenant = create_test_tenant(db)

        requester = create_user(
            db,
            email=f"requester-{uuid4()}@example.com",
        )

        approver = create_user(
            db,
            email=f"approver-{uuid4()}@example.com",
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=requester.id,
            role=Role.ANALYST,
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=approver.id,
            role=Role.REVIEWER,
        )

        workflow = ApprovalWorkflow(
            ApprovalAuthorizationService(db)
        )

        approval = workflow.request_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{uuid4()}",
        )

        result = workflow.approve(
            approval_id=approval.id,
            approver_id=approver.id,
        )

        assert result.status == "approved"
        assert result.approved is True
        assert result.approver_id == approver.id

    finally:
        db.close()


def test_non_approver_cannot_approve():
    db = SessionLocal()

    try:
        tenant = create_test_tenant(db)

        requester = create_user(
            db,
            email=f"requester-{uuid4()}@example.com",
        )

        unauthorized_user = create_user(
            db,
            email=f"user-{uuid4()}@example.com",
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=requester.id,
            role=Role.ANALYST,
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=unauthorized_user.id,
            role=Role.ANALYST,
        )

        workflow = ApprovalWorkflow(
            ApprovalAuthorizationService(db)
        )

        approval = workflow.request_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{uuid4()}",
        )

        with pytest.raises(PermissionError):
            workflow.approve(
                approval_id=approval.id,
                approver_id=unauthorized_user.id,
            )

        db.refresh(approval)

        assert approval.status == "pending"
        assert approval.approver_id is None

    finally:
        db.close()