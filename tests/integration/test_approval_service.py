from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.approvals.service import ApprovalAuthorizationService
from app.common.db.models import Tenant, User, TenantMembership
from app.tenants.repository import TenantRepository
from app.common.db.session import SessionLocal
from app.policies.rbac import Role

def create_test_tenant(db: Session):
    tenant = Tenant(
        name=f"Approval Test Tenant {uuid4()}",
        slug=f"approval-test-{uuid4()}",
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_test_user(db: Session):
    user = User(
        email=f"user-{uuid4()}@example.com",
        display_name="Approval Test User",
        password_hash="test-password",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_membership(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    role: str,
):
    membership = TenantMembership(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
        status="active",
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership

def test_approval_authorization_service():
    db = SessionLocal()

    try:
        tenant_repository = TenantRepository(db)

        tenant = tenant_repository.create(
            name="Approval Service Test Tenant",
            slug=f"approval-service-{uuid4()}",
        )

        approver = User(
            email=f"approver-{uuid4()}@example.com",
            display_name="Test Approver",
            password_hash="test",
        )

        requester = User(
            email=f"requester-{uuid4()}@example.com",
            display_name="Test Requester",
            password_hash="test",
        )

        db.add_all([approver, requester])
        db.commit()

        db.refresh(approver)
        db.refresh(requester)

        db.add_all(
            [
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=approver.id,
                    role=Role.REVIEWER.value,
                    status="active",
                ),
                TenantMembership(
                    tenant_id=tenant.id,
                    user_id=requester.id,
                    role=Role.ANALYST.value,
                    status="active",
                ),
            ]
        )

        db.commit()

        service = ApprovalAuthorizationService(db)

        assert service.can_approve(
            tenant_id=tenant.id,
            user_id=approver.id,
        )

        assert not service.can_execute(
            tenant_id=tenant.id,
            user_id=approver.id,
        )

        assert service.can_execute(
            tenant_id=tenant.id,
            user_id=requester.id,
        )

        assert not service.can_approve(
            tenant_id=tenant.id,
            user_id=requester.id,
        )

    finally:
        db.close()

def test_create_pending_approval():
    db = SessionLocal()

    suffix = uuid4()

    try:
        tenant = TenantRepository(db).create(
            name="Approval Service Test Tenant",
            slug=f"approval-service-test-{suffix}",
        )

        requester = User(
            email=f"requester-{suffix}@example.com",
            display_name="Requester",
            password_hash="test",
        )

        db.add(requester)
        db.commit()
        db.refresh(requester)

        db.add(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=requester.id,
                role=Role.ANALYST.value,
                status="active",
            )
        )
        db.commit()

        service = ApprovalAuthorizationService(db)

        approval = service.create_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{suffix}",
        )

        assert approval.id is not None
        assert approval.tenant_id == tenant.id
        assert approval.requester_id == requester.id
        assert approval.approver_id is None
        assert approval.approved is False
        assert approval.status == "pending"
        assert approval.thread_id == f"thread-{suffix}"

    finally:
        db.close()


def test_get_pending_approval_returns_pending_approval():
    db = SessionLocal()

    suffix = uuid4()

    try:
        tenant = TenantRepository(db).create(
            name="Pending Approval Test Tenant",
            slug=f"pending-approval-test-{suffix}",
        )

        requester = User(
            email=f"pending-requester-{suffix}@example.com",
            display_name="Requester",
            password_hash="test",
        )

        db.add(requester)
        db.commit()
        db.refresh(requester)

        db.add(
            TenantMembership(
                tenant_id=tenant.id,
                user_id=requester.id,
                role=Role.ANALYST.value,
                status="active",
            )
        )
        db.commit()

        service = ApprovalAuthorizationService(db)

        approval = service.create_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"pending-thread-{suffix}",
        )

        loaded = service.get_pending_approval(approval.id)

        assert loaded is not None
        assert loaded.id == approval.id
        assert loaded.status == "pending"

    finally:
        db.close()


def test_get_pending_approval_returns_none_for_completed_approval():
    db = SessionLocal()

    suffix = uuid4()

    try:
        tenant = TenantRepository(db).create(
            name="Completed Approval Test Tenant",
            slug=f"completed-approval-test-{suffix}",
        )

        requester = User(
            email=f"completed-requester-{suffix}@example.com",
            display_name="Requester",
            password_hash="test",
        )

        approver = User(
            email=f"completed-approver-{suffix}@example.com",
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

        service = ApprovalAuthorizationService(db)

        approval = service._repository.create(
            tenant_id=tenant.id,
            requester_id=requester.id,
            approver_id=approver.id,
            approved=True,
            status="approved",
            thread_id=f"completed-thread-{suffix}",
        )

        loaded = service.get_pending_approval(approval.id)

        assert loaded is None

    finally:
        db.close()

def test_record_approved_decision():
    db = SessionLocal()

    try:
        tenant = create_test_tenant(db)
        requester = create_test_user(db)
        approver = create_test_user(db)

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=requester.id,
            role=Role.ANALYST.value,
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=approver.id,
            role=Role.REVIEWER.value,
        )

        service = ApprovalAuthorizationService(db)

        approval = service.create_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{uuid4()}",
        )

        result = service.record_decision(
            approval_id=approval.id,
            approver_id=approver.id,
            approved=True,
        )

        assert result is not None
        assert result.status == "approved"
        assert result.approver_id == approver.id

    finally:
        db.close()


def test_record_rejected_decision():
    db: Session = SessionLocal()

    try:
        tenant = create_test_tenant(db)
        requester = create_test_user(db)
        approver = create_test_user(db)

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=requester.id,
            role=Role.ANALYST.value,
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=approver.id,
            role=Role.REVIEWER.value,
        )

        service = ApprovalAuthorizationService(db)

        approval = service.create_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{uuid4()}",
        )

        result = service.record_decision(
            approval_id=approval.id,
            approver_id=approver.id,
            approved=False,
        )

        assert result is not None
        assert result.status == "rejected"
        assert result.approver_id == approver.id

    finally:
        db.close()


def test_unauthorized_user_cannot_record_decision():
    db: Session = SessionLocal()

    try:
        tenant = create_test_tenant(db)
        requester = create_test_user(db)
        unauthorized_user = create_test_user(db)

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=requester.id,
            role=Role.ANALYST.value,
        )

        create_membership(
            db,
            tenant_id=tenant.id,
            user_id=unauthorized_user.id,
            role=Role.ANALYST.value,
        )

        service = ApprovalAuthorizationService(db)

        approval = service.create_approval(
            tenant_id=tenant.id,
            requester_id=requester.id,
            thread_id=f"thread-{uuid4()}",
        )

        result = service.record_decision(
            approval_id=approval.id,
            approver_id=unauthorized_user.id,
            approved=True,
        )

        assert result is None

        pending = service.get_pending_approval(approval.id)

        assert pending is not None
        assert pending.status == "pending"
        assert pending.approver_id is None

    finally:
        db.close()