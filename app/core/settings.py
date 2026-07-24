import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Resolved relative to the project root (three levels above this file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_DB_PATH = _PROJECT_ROOT / "data" / "arbitrage.db"


@dataclass(frozen=True)
class Settings:
    """
    Centralized application configuration.

    All values can be overridden by environment variables with the
    ARBITRAGE_ prefix. database_path is always a pathlib.Path regardless
    of whether the value came from the default or an env var.

    frozen=True: Settings instances are immutable after construction.
    Use get_settings() to obtain the cached singleton. Call
    get_settings.cache_clear() in tests to force re-evaluation after
    changing environment variables via monkeypatch.
    """
    app_name: str
    app_version: str
    app_description: str
    environment: str
    database_path: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the application settings singleton.

    Reads environment variables once and caches the result. Subsequent
    calls return the cached instance without re-reading the environment.

    To force re-evaluation in tests after changing environment variables:
        get_settings.cache_clear()
    """
    return Settings(
        app_name=os.getenv(
            "ARBITRAGE_APP_NAME",
            "Amazon Arbitrage Sourcing Platform",
        ),
        app_version=os.getenv(
            "ARBITRAGE_APP_VERSION",
            "0.1.0",
        ),
        app_description=os.getenv(
            "ARBITRAGE_APP_DESCRIPTION",
            "Evaluate retail products for Amazon arbitrage profitability "
            "and preserve evaluation history.",
        ),
        environment=os.getenv(
            "ARBITRAGE_ENVIRONMENT",
            "development",
        ),
        database_path=Path(
            os.getenv(
                "ARBITRAGE_DATABASE_PATH",
                str(_DEFAULT_DB_PATH),
            )
        ),
    )