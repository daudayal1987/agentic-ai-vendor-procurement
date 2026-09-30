from uuid import uuid4

from app.policies.tool_policy import ToolPolicy
from app.tenants.context import TenantContext


def test_search_documents_requires_document_read() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=(),
        enabled_services=("document_search"),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "missing permission: document:read"

def test_search_documents_allows_document_read() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search"),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is True

def test_unknown_tool_is_denied() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search"),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="unknown_tool",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "unknown tool: unknown_tool"


def test_tool_denied_when_user_is_missing() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=None,
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search"),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "missing user"


def test_tool_denied_when_tenant_is_missing() -> None:
    context = TenantContext(
        tenant_id=None,
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search"),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "missing tenant"


def test_tool_denied_when_role_is_missing() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=(),
        permissions=("document:read",),
        enabled_services=("document_search"),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "missing role"

def test_tool_denied_when_service_is_disabled() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=(),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "service disabled: document_search"


def test_tool_denied_for_resource_owned_by_another_tenant() -> None:
    tenant_id = uuid4()

    context = TenantContext(
        tenant_id=tenant_id,
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
        resource_tenant_id=uuid4(),
    )

    assert decision.allowed is False
    assert decision.reason == "resource belongs to another tenant"

def test_tool_allows_resource_owned_by_same_tenant() -> None:
    tenant_id = uuid4()

    context = TenantContext(
        tenant_id=tenant_id,
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
        resource_tenant_id=tenant_id,
    )

    assert decision.allowed is True
    assert decision.reason is None

def test_registered_tool_without_permission_is_denied() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=(),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
    )

    assert decision.allowed is False
    assert decision.reason == "missing permission: document:read"

def test_tool_denied_for_different_resource_tenant() -> None:
    tenant_id = uuid4()

    context = TenantContext(
        tenant_id=tenant_id,
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    decision = policy.check(
        tool_name="search_documents",
        tenant_context=context,
        resource_tenant_id=uuid4(),
    )

    assert decision.allowed is False
    assert decision.reason == "resource belongs to another tenant"