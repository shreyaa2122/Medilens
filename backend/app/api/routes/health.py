from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import ApiResponse, HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ApiResponse[HealthStatus])
def health_check() -> ApiResponse[HealthStatus]:
    settings = get_settings()
    return ApiResponse(
        data=HealthStatus(
            status="ok",
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )
    )
