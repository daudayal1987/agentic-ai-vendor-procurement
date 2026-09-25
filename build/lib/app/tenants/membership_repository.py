from uuid import UUID

from sqlalchemy.orm import Session

from app.common.db.models import TenantMembership


class TenantMembershipRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_membership(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> TenantMembership | None:
        return (
            self.session.query(TenantMembership)
            .filter(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
                TenantMembership.status == "active",
            )
            .first()
        )