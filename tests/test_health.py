import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.settings import get_settings


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /health — status and shape
# ---------------------------------------------------------------------------

def test_health_returns_200():
    """GET /health must return HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_status_is_ok():
    """The status field must equal 'ok'."""
    data = client.get("/health").json()
    assert data["status"] == "ok"


def test_health_response_contains_application():
    """The application field must be present and non-empty."""
    data = client.get("/health").json()
    assert "application" in data
    assert data["application"]


def test_health_response_contains_version():
    """The version field must be present and non-empty."""
    data = client.get("/health").json()
    assert "version" in data
    assert data["version"]


def test_health_response_contains_environment():
    """The environment field must be present and non-empty."""
    data = client.get("/health").json()
    assert "environment" in data
    assert data["environment"]


def test_health_response_application_matches_settings():
    """The application field must equal the configured app_name."""
    data = client.get("/health").json()
    assert data["application"] == get_settings().app_name


def test_health_response_version_matches_settings():
    """The version field must equal the configured app_version."""
    data = client.get("/health").json()
    assert data["version"] == get_settings().app_version


def test_health_response_environment_matches_settings():
    """The environment field must equal the configured environment."""
    data = client.get("/health").json()
    assert data["environment"] == get_settings().environment


def test_health_does_not_expose_database_path():
    """
    The health response must not include database_path or any other
    sensitive infrastructure detail. Only status, application, version,
    and environment are permitted.
    """
    data = client.get("/health").json()
    assert "database_path" in get_settings().__dataclass_fields__
    assert "database_path" not in data


def test_health_response_has_exactly_four_fields():
    """
    The health response must contain exactly the four documented fields:
    status, application, version, environment.
    No undocumented fields should leak through.
    """
    data = client.get("/health").json()
    assert set(data.keys()) == {"status", "application", "version", "environment"}


# ---------------------------------------------------------------------------
# FastAPI application metadata
# ---------------------------------------------------------------------------

def test_fastapi_app_title_matches_settings():
    """
    The FastAPI app title must match the configured app_name.
    This confirms main.py passes settings values to the FastAPI constructor
    rather than hardcoding them.
    """
    assert app.title == get_settings().app_name


def test_fastapi_app_version_matches_settings():
    """
    The FastAPI app version must match the configured app_version.
    """
    assert app.version == get_settings().app_version