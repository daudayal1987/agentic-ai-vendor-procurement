from app.policies.rbac import (
    Permission,
    Role,
    has_permission,
)


def test_admin_can_manage_tenant():
    assert has_permission(
        Role.ADMIN,
        Permission.TENANT_MANAGE,
    )


def test_analyst_can_run_analysis():
    assert has_permission(
        Role.ANALYST,
        Permission.ANALYSIS_RUN,
    )


def test_analyst_cannot_review_approval():
    assert not has_permission(
        Role.ANALYST,
        Permission.APPROVAL_REVIEW,
    )


def test_reviewer_can_review_approval():
    assert has_permission(
        Role.REVIEWER,
        Permission.APPROVAL_REVIEW,
    )