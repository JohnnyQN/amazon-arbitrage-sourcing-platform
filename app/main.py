from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.routes import router
from app.core.settings import get_settings

# Settings are read once at startup and passed to FastAPI.
# The app object's title, version, and description are fixed at
# construction time from the cached settings.
_settings = get_settings()

app = FastAPI(
    title=_settings.app_name,
    version=_settings.app_version,
    description=_settings.app_description,
)

# Health check registered first so /health resolves before
# the sourcing domain routes.
app.include_router(health_router)
app.include_router(router)