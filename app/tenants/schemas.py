from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TenantCreateRequest(BaseModel):
    name: str
    slug: str


class TenantCreateResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

class TenantGetResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }