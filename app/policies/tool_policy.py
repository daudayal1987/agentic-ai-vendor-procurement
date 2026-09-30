from dataclasses import dataclass
from uuid import UUID

from app.policies.rbac import Permission
from app.tenants.context import TenantContext

TOOL_POLICIES = {
    "search_documents": {
        "permission": Permission.DOCUMENT_READ.value,
        "service": "document_search",
    },
    "save_memory": {},
    "search_memory": {},
}

@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str | None = None


class ToolPolicy:

    def check(
        self,
        tool_name: str,
        tenant_context: TenantContext,
        resource_tenant_id: UUID | None = None,
    ) -> PolicyDecision:
        
        if tenant_context.user_id is None:
            return PolicyDecision(
                allowed=False,
                reason="missing user",
            )

        if not tenant_context.tenant_id:
            return PolicyDecision(
                allowed=False,
                reason="missing tenant",
            )

        if not tenant_context.roles:
            return PolicyDecision(
                allowed=False,
                reason="missing role",
            )

        if (
            resource_tenant_id is not None
            and resource_tenant_id != tenant_context.tenant_id
        ):
            return PolicyDecision(
                allowed=False,
                reason="resource belongs to another tenant",
            )

        rule = TOOL_POLICIES.get(tool_name)

        if rule is None:
            return PolicyDecision(
                allowed=False,
                reason=f"unknown tool: {tool_name}",
            )

        service = rule.get("service")

        if (
            service is not None
            and service not in tenant_context.enabled_services
        ):
            return PolicyDecision(
                allowed=False,
                reason=f"service disabled: {service}",
            )

        permission = rule.get("permission")

        if (
            permission is not None
            and permission not in tenant_context.permissions
        ):
            return PolicyDecision(
                allowed=False,
                reason=f"missing permission: {permission}",
            )

        return PolicyDecision(allowed=True)