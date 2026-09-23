from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.db.session import get_db
from app.policies.rbac import Permission, Role, has_permission
from app.tenants.context import TenantContext
from app.tenants.dependencies import get_tenant_context
from app.tenants.membership_repository import TenantMembershipRepository
from app.auth.dependencies import get_current_principal
from app.auth.principal import AuthenticatedPrincipal


def require_permission(permission: Permission):
    def dependency(
        tenant_context: TenantContext = Depends(get_tenant_context),
        principal: AuthenticatedPrincipal = Depends(get_current_principal),
        db: Session = Depends(get_db),
    ) -> TenantContext:

        membership_repository = TenantMembershipRepository(db)

        membership = membership_repository.get_active_membership(
            tenant_id=tenant_context.tenant_id,
            user_id=principal.user_id,
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not an active member of this tenant",
            )

        try:
            role = Role(membership.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid tenant role",
            )

        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return TenantContext(
            tenant_id=tenant_context.tenant_id,
            user_id=principal.user_id,
            roles=(role.value,),
            permissions=tuple(
                permission.value
                for permission in Permission
                if has_permission(role, permission)
            ),
        )

    return dependency