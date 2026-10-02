from uuid import uuid4

from app.approvals.repository import ApprovalAuditRepository
from app.common.db.models import TenantMembership, User
from app.common.db.session import SessionLocal
from app.policies.rbac import Role
from app.tenants.repository import TenantRepository


def test_create_and_get_approval_audit():
    db = SessionLocal()

    suffix = uuid4()

    try:
        tenant = TenantRepository(db).create(
            name="Approval Test Tenant",
            slug=f"approval-test-tenant-{suffix}",
        )

        requester = User(
            email=f"approval-requester-{suffix}@example.com",
            display_name="Requester",
            password_hash="test",
        )

        approver = User(
            email=f"approval-approver-{suffix}@example.com",
            display_name="Approver",
            password_hash="test",
        )

        db.add_all([requester, approver])
        db.commit()

        db.refresh(requester)
        db.refresh(approver)

        db.add_all(
            [
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=requester.id,
                    role=Role.ANALYST.value,
                    status="active",
                ),
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=approver.id,
                    role=Role.REVIEWER.value,
                    status="active",
                ),
            ]
        )
        db.commit()

        repository = ApprovalAuditRepository(db)

        audit = repository.create(
            tenant_id=tenant.id,
            requester_id=requester.id,
            approver_id=approver.id,
            approved=True,
            status="approved",
            thread_id=f"hitl-test-thread-{suffix}"
        )

        assert audit.id is not None
        assert audit.tenant_id == tenant.id
        assert audit.requester_id == requester.id
        assert audit.approver_id == approver.id
        assert audit.approved is True
        assert audit.status == "approved"
        assert audit.thread_id == f"hitl-test-thread-{suffix}"

        loaded = repository.get_by_id(audit.id)

        assert loaded is not None
        assert loaded.id == audit.id

        loaded_by_thread = repository.get_by_thread_id(f"hitl-test-thread-{suffix}")

        assert loaded_by_thread is not None
        assert loaded_by_thread.id == audit.id

    finally:
        db.close()