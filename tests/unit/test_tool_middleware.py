from uuid import uuid4

from app.policies.tool_policy import ToolPolicy
from app.tenants.context import TenantContext

from app.agents.middleware import ToolExecutionMiddleware


def test_middleware_blocks_denied_tool() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=(),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    executed = False

    def tool() -> str:
        nonlocal executed
        executed = True
        return "executed"

    # Middleware doesn't exist yet.
    middleware = ToolExecutionMiddleware(
        policy=policy,
        tenant_context=context,
    )

    result = middleware.execute(
        tool_name="search_documents",
        tool=tool,
    )

    assert result.allowed is False
    assert executed is False


def test_middleware_executes_allowed_tool() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    executed = False

    def tool() -> str:
        nonlocal executed
        executed = True
        return "executed"

    middleware = ToolExecutionMiddleware(
        policy=policy,
        tenant_context=context,
    )

    result = middleware.execute(
        tool_name="search_documents",
        tool=tool,
    )

    assert result.allowed is True
    assert result.result == "executed"
    assert result.reason is None
    assert executed is True


def test_middleware_passes_tool_arguments() -> None:
    context = TenantContext(
        tenant_id=uuid4(),
        user_id=uuid4(),
        roles=("analyst",),
        permissions=("document:read",),
        enabled_services=("document_search",),
    )

    policy = ToolPolicy()

    def tool(query: str) -> str:
        return query

    middleware = ToolExecutionMiddleware(
        policy=policy,
        tenant_context=context,
    )

    result = middleware.execute(
        tool_name="search_documents",
        tool=tool,
        query="contract",
    )

    assert result.allowed is True
    assert result.result == "contract"