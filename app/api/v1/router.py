from fastapi import APIRouter

from app.api.v1.tenant import router as tenant_router

api_v1_router = APIRouter(
    prefix="/api/v1",
)

api_v1_router.include_router(tenant_router)