from uuid import UUID

from sqlalchemy.orm import Session

from app.common.db.models import Tenant


class TenantScopedRepository:
    def __init__(
        self,
        session: Session,
        tenant_id: UUID,
    ):
        self.session = session
        self.tenant_id = tenant_id

    def get_current_tenant(self) -> Tenant | None:
        return (
            self.session.query(Tenant)
            .filter(
                Tenant.id == self.tenant_id,
            )
            .first()
        )

    def get_tenant(
        self,
        tenant_id: UUID,
    ) -> Tenant | None:
        if tenant_id != self.tenant_id:
            return None

        return (
            self.session.query(Tenant)
            .filter(
                Tenant.id == self.tenant_id,
            )
            .first()
        )