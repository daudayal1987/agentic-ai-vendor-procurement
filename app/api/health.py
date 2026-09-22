from fastapi import APIRouter

from app.api.schemas import HealthResponse, ReadinessResponse
from app.services.health_service import get_health_status, get_readiness_status


router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/health",
    response_model=HealthResponse
)
def health_check():
    return get_health_status()



@router.get(
    "/readiness",
    response_model=ReadinessResponse
)
def readiness_check():
    return get_readiness_status()