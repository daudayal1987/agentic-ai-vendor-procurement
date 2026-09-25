from uuid import UUID

from sqlalchemy.orm import Session

from app.common.db.models import Tenant


class TenantRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        name: str,
        slug: str,
    ) -> Tenant:
        tenant = Tenant(
            name=name,
            slug=slug,
        )

        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)

        return tenant

    def get_by_id(
        self,
        tenant_id: UUID,
    ) -> Tenant | None:
        return self.session.get(
            Tenant,
            tenant_id,
        )

    def get_by_slug(
        self,
        slug: str,
    ) -> Tenant | None:
        return (
            self.session.query(Tenant)
            .filter(Tenant.slug == slug)
            .first()
        )