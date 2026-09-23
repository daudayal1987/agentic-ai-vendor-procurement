from sqlalchemy.orm import Session

from app.common.db.session import SessionLocal
from app.common.db.models import User, TenantMembership
from app.tenants.repository import TenantRepository
from app.tenants.membership_repository import TenantMembershipRepository
from app.policies.rbac import Permission, Role, has_permission


def main() -> None:
    db: Session = SessionLocal()

    try:
        tenant_repository = TenantRepository(db)

        tenant = tenant_repository.create(
            name="Authorization Test Tenant",
            slug="authorization-test-tenant",
        )

        user = User(
            email="analyst@example.com",
            display_name="Test Analyst",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user.id,
            role=Role.ANALYST.value,
            status="active",
        )

        db.add(membership)
        db.commit()

        membership_repository = TenantMembershipRepository(db)

        result = membership_repository.get_active_membership(
            tenant_id=tenant.id,
            user_id=user.id,
        )

        assert result is not None
        assert result.role == Role.ANALYST.value

        assert has_permission(
            Role.ANALYST,
            Permission.ANALYSIS_RUN,
        )

        assert not has_permission(
            Role.ANALYST,
            Permission.APPROVAL_REVIEW,
        )

        print("Membership lookup: PASSED")
        print("Analyst analysis permission: PASSED")
        print("Analyst approval restriction: PASSED")

    finally:
        db.close()


if __name__ == "__main__":
    main()