from uuid import uuid4

from app.approvals.service import ApprovalAuthorizationService


def test_reviewer_can_approve(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()

    monkeypatch.setattr(
        "app.approvals.service.has_tenant_permission",
        lambda **kwargs: True,
    )

    service = ApprovalAuthorizationService(db=None)

    assert service.can_approve(
        tenant_id=tenant_id,
        user_id=user_id,
    ) is True


def test_user_without_approval_permission_cannot_approve(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()

    monkeypatch.setattr(
        "app.approvals.service.has_tenant_permission",
        lambda **kwargs: False,
    )

    service = ApprovalAuthorizationService(db=None)

    assert service.can_approve(
        tenant_id=tenant_id,
        user_id=user_id,
    ) is False


def test_approval_authorization_is_tenant_scoped(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()

    captured = {}

    def fake_has_tenant_permission(**kwargs):
        captured.update(kwargs)
        return True

    monkeypatch.setattr(
        "app.approvals.service.has_tenant_permission",
        fake_has_tenant_permission,
    )

    service = ApprovalAuthorizationService(db=None)

    service.can_approve(
        tenant_id=tenant_id,
        user_id=user_id,
    )

    assert captured["tenant_id"] == tenant_id
    assert captured["user_id"] == user_id

    from app.policies.rbac import Permission

    assert captured["permission"] == Permission.APPROVAL_REVIEW


def test_different_users_are_checked_independently(monkeypatch):
    tenant_id = uuid4()
    reviewer_id = uuid4()
    analyst_id = uuid4()

    authorized_users = {reviewer_id}

    def fake_has_tenant_permission(**kwargs):
        return kwargs["user_id"] in authorized_users

    monkeypatch.setattr(
        "app.approvals.service.has_tenant_permission",
        fake_has_tenant_permission,
    )

    service = ApprovalAuthorizationService(db=None)

    assert service.can_approve(
        tenant_id=tenant_id,
        user_id=reviewer_id,
    ) is True

    assert service.can_approve(
        tenant_id=tenant_id,
        user_id=analyst_id,
    ) is False
