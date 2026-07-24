from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """
    Response model for GET /health.

    Contains only safe, non-sensitive fields suitable for deployment
    health checks. Does not expose database paths or secrets.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "application": "Amazon Arbitrage Sourcing Platform",
                "version": "0.1.0",
                "environment": "development",
            }
        }
    )

    status: str
    application: str
    version: str
    environment: str