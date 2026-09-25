from fastapi import APIRouter, Depends

from app.auth.authorization import require_permission
from app.policies.rbac import Permission
from app.tenants.context import TenantContext

router = APIRouter(
    prefix="/tenant",
    tags=["Tenant"]
)

@router.get("/protected")
def protected_endpoint(
    context: TenantContext = Depends(
        require_permission(Permission.TENANT_READ)
    ),
):
    return {
        "message": "Access granted",
        "tenant_id": str(context.tenant_id),
        "user_id": str(context.user_id),
        "roles": list(context.roles),
        "permissions": list(context.permissions),
    }