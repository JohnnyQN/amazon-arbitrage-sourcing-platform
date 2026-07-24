from fastapi import APIRouter

from app.core.settings import get_settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Lightweight liveness probe for deployment readiness checks. "
        "Returns application metadata without querying the database. "
        "Does not expose infrastructure details or secrets."
    ),
    tags=["Health"],
)
def health_check():
    """Return application status and metadata."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )