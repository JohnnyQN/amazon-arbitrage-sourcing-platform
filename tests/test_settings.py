import pytest
from pathlib import Path

from app.core.settings import Settings, get_settings


# ---------------------------------------------------------------------------
# Fixture — clear the lru_cache before and after every test in this module
# so monkeypatched environment variables take effect and don't leak.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Clear the get_settings() lru_cache before and after each test.

    Without this, the first test that calls get_settings() populates
    the cache and all subsequent tests in the session see that value
    even after monkeypatching environment variables.
    """
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

def test_default_app_name():
    """Default app_name matches the documented project name."""
    assert get_settings().app_name == "Amazon Arbitrage Sourcing Platform"


def test_default_app_version():
    """Default version is the current release string."""
    assert get_settings().app_version == "0.1.0"


def test_default_app_description():
    """Default description mentions both core features."""
    description = get_settings().app_description
    assert "arbitrage" in description.lower()
    assert "evaluation" in description.lower()


def test_default_environment():
    """Default environment is development."""
    assert get_settings().environment == "development"


def test_default_database_path_points_to_data_directory():
    """Default database_path ends with data/arbitrage.db."""
    path = get_settings().database_path
    # Use parts to avoid platform path-separator differences
    assert path.parts[-1] == "arbitrage.db"
    assert path.parts[-2] == "data"


def test_database_path_is_path_instance():
    """database_path must be a pathlib.Path, not a plain string."""
    assert isinstance(get_settings().database_path, Path)


def test_settings_is_frozen_dataclass():
    """Settings instances must be immutable — assignment must raise."""
    settings = get_settings()
    with pytest.raises((AttributeError, TypeError)):
        settings.app_name = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Environment variable overrides
# ---------------------------------------------------------------------------

def test_env_var_overrides_app_name(monkeypatch):
    """
    ARBITRAGE_APP_NAME must override the default app_name.
    The cache is cleared by the autouse fixture before this test runs,
    so get_settings() reads the monkeypatched value.
    """
    monkeypatch.setenv("ARBITRAGE_APP_NAME", "Test Platform")
    settings = get_settings()
    assert settings.app_name == "Test Platform"


def test_env_var_overrides_app_version(monkeypatch):
    """ARBITRAGE_APP_VERSION must override the default version."""
    monkeypatch.setenv("ARBITRAGE_APP_VERSION", "9.9.9")
    assert get_settings().app_version == "9.9.9"


def test_env_var_overrides_environment(monkeypatch):
    """ARBITRAGE_ENVIRONMENT must override the default environment."""
    monkeypatch.setenv("ARBITRAGE_ENVIRONMENT", "production")
    assert get_settings().environment == "production"


def test_env_var_overrides_database_path(monkeypatch, tmp_path):
    """
    ARBITRAGE_DATABASE_PATH must override the default database path.
    The result must still be a Path instance pointing to the given location.
    """
    custom_path = tmp_path / "custom.db"
    monkeypatch.setenv("ARBITRAGE_DATABASE_PATH", str(custom_path))

    settings = get_settings()

    assert settings.database_path == custom_path
    assert isinstance(settings.database_path, Path)


# ---------------------------------------------------------------------------
# Cache behavior
# ---------------------------------------------------------------------------

def test_cache_returns_same_instance():
    """
    Repeated calls to get_settings() without clearing the cache must
    return the exact same object — not a new instance each time.
    """
    first = get_settings()
    second = get_settings()
    assert first is second


def test_cache_clear_picks_up_new_env_var(monkeypatch):
    """
    After cache_clear(), get_settings() must re-read environment variables.
    This is the pattern tests use to isolate settings between calls.
    """
    original_name = get_settings().app_name

    monkeypatch.setenv("ARBITRAGE_APP_NAME", "Overridden Name")
    get_settings.cache_clear()

    assert get_settings().app_name == "Overridden Name"
    assert get_settings().app_name != original_name


# ---------------------------------------------------------------------------
# Repository dependency integration
# ---------------------------------------------------------------------------

def test_get_evaluation_repository_uses_configured_database_path(
    monkeypatch, tmp_path
):
    """
    get_evaluation_repository() must use get_settings().database_path
    rather than a hardcoded path. When the settings path is overridden,
    the returned repository must target the overridden location.

    This test does not write to data/arbitrage.db.
    """
    from app.api.dependencies import get_evaluation_repository

    custom_db = tmp_path / "dependency_test.db"
    monkeypatch.setenv("ARBITRAGE_DATABASE_PATH", str(custom_db))
    get_settings.cache_clear()

    repo = get_evaluation_repository()

    assert repo.db_path == custom_db