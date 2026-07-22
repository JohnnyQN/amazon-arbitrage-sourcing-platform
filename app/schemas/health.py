from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Response model for GET /health.

    Contains only safe, non-sensitive fields suitable for deployment
    health checks. Does not expose database paths or secrets.
    """
    status: str
    application: str
    version: str
    environment: str