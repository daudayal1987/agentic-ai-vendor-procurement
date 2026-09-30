from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.policies.tool_policy import PolicyDecision, ToolPolicy
from app.tenants.context import TenantContext


@dataclass(frozen=True)
class ToolExecutionResult:
    allowed: bool
    result: Any = None
    reason: str | None = None


class ToolExecutionMiddleware:

    def __init__(
        self,
        policy: ToolPolicy,
        tenant_context: TenantContext,
    ) -> None:
        self._policy = policy
        self._tenant_context = tenant_context

    def execute(
        self,
        tool_name: str,
        tool: Callable[[], Any],
        **kwargs: Any,
    ) -> ToolExecutionResult:

        decision: PolicyDecision = self._policy.check(
            tool_name=tool_name,
            tenant_context=self._tenant_context,
        )

        if not decision.allowed:
            return ToolExecutionResult(
                allowed=False,
                reason=decision.reason,
            )

        result = tool(**kwargs)

        return ToolExecutionResult(
            allowed=True,
            result=result,
        )