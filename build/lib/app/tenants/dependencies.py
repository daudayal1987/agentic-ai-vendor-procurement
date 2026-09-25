from uuid import UUID

from fastapi import Header

from app.tenants.context import TenantContext


def get_tenant_context(
    x_tenant_id: UUID = Header(...),
) -> TenantContext:
    return TenantContext(
        tenant_id=x_tenant_id,
    )