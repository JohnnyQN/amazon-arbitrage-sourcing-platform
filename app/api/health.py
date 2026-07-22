from fastapi import APIRouter

from app.core.settings import get_settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Lightweight health check endpoint for deployment readiness probes.

    Returns 200 when the application process is running. Does not
    perform a database query — infrastructure health is separate from
    application health. Does not expose database paths or secrets.
    """
    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )