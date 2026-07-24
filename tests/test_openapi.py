from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app

client = TestClient(app)


def _schema() -> dict:
    """Fetch and return the OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# Schema accessibility and metadata
# ---------------------------------------------------------------------------

def test_openapi_schema_is_accessible():
    """GET /openapi.json must return 200 and valid JSON."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "info" in data
    assert "paths" in data


def test_openapi_title_matches_settings():
    """OpenAPI info.title must equal the configured app_name."""
    schema = _schema()
    assert schema["info"]["title"] == get_settings().app_name


def test_openapi_version_matches_settings():
    """OpenAPI info.version must equal the configured app_version."""
    schema = _schema()
    assert schema["info"]["version"] == get_settings().app_version


# ---------------------------------------------------------------------------
# All five endpoints present
# ---------------------------------------------------------------------------

def test_openapi_contains_health_endpoint():
    """GET /health must appear in the OpenAPI path list."""
    assert "/health" in _schema()["paths"]


def test_openapi_contains_evaluate_endpoint():
    """POST /evaluate must appear in the OpenAPI path list."""
    assert "/evaluate" in _schema()["paths"]


def test_openapi_contains_evaluations_list_endpoint():
    """GET /evaluations must appear in the OpenAPI path list."""
    assert "/evaluations" in _schema()["paths"]


def test_openapi_contains_evaluations_by_id_endpoint():
    """GET /evaluations/{evaluation_id} must appear in the path list."""
    assert "/evaluations/{evaluation_id}" in _schema()["paths"]


def test_openapi_contains_evaluations_by_asin_endpoint():
    """GET /evaluations/asin/{asin} must appear in the path list."""
    assert "/evaluations/asin/{asin}" in _schema()["paths"]


# ---------------------------------------------------------------------------
# HTTP methods
# ---------------------------------------------------------------------------

def test_evaluate_endpoint_uses_post_method():
    """POST /evaluate must be registered as a POST operation."""
    assert "post" in _schema()["paths"]["/evaluate"]


def test_health_endpoint_uses_get_method():
    """GET /health must be registered as a GET operation."""
    assert "get" in _schema()["paths"]["/health"]


def test_evaluations_list_uses_get_method():
    """GET /evaluations must be registered as a GET operation."""
    assert "get" in _schema()["paths"]["/evaluations"]


# ---------------------------------------------------------------------------
# Summaries present
# ---------------------------------------------------------------------------

def test_evaluate_endpoint_has_summary():
    """POST /evaluate must have a non-empty summary for Swagger display."""
    summary = _schema()["paths"]["/evaluate"]["post"].get("summary", "")
    assert summary


def test_health_endpoint_has_summary():
    """GET /health must have a non-empty summary for Swagger display."""
    summary = _schema()["paths"]["/health"]["get"].get("summary", "")
    assert summary


def test_evaluations_list_has_summary():
    """GET /evaluations must have a non-empty summary."""
    summary = _schema()["paths"]["/evaluations"]["get"].get("summary", "")
    assert summary


def test_evaluations_by_id_has_summary():
    """GET /evaluations/{evaluation_id} must have a non-empty summary."""
    summary = (
        _schema()["paths"]["/evaluations/{evaluation_id}"]["get"].get("summary", "")
    )
    assert summary


def test_evaluations_by_asin_has_summary():
    """GET /evaluations/asin/{asin} must have a non-empty summary."""
    summary = (
        _schema()["paths"]["/evaluations/asin/{asin}"]["get"].get("summary", "")
    )
    assert summary