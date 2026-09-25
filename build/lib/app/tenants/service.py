from sqlalchemy.orm import Session

from app.tenants.repository import TenantRepository
from app.tenants.schemas import TenantCreateRequest, TenantCreateResponse, TenantGetResponse


class TenantService:
    def __init__(self, session: Session):
        self.repository = TenantRepository(session)

    def create_tenant(
        self,
        payload: TenantCreateRequest,
    ) -> TenantCreateResponse:
        tenant = self.repository.create(
            name=payload.name,
            slug=payload.slug,
        )

        return TenantCreateResponse.model_validate(
            tenant
        )