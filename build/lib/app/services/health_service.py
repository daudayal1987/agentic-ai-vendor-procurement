from app.api.schemas import HealthResponse, ReadinessResponse
from app.common.config import Settings

settings = Settings()

def get_health_status() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
    )

def get_readiness_status() -> ReadinessResponse:
    return ReadinessResponse(
        status="ready",
        environment=settings.app_env,
    )