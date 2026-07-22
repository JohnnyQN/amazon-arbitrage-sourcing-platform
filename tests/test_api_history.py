import pytest
from datetime import datetime
from pathlib import Path
from fastapi.testclient import TestClient

from app.api.dependencies import get_evaluation_repository
from app.main import app
from app.repositories.evaluation_repository import EvaluationRepository


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client_and_repo(tmp_path: Path):
    """
    Provides a TestClient with the EvaluationRepository dependency
    overridden to use a temporary database unique to each test.

    Uses try/finally to remove only the get_evaluation_repository override
    so no other dependency overrides are disturbed. TestClient is used as a
    context manager so its lifespan is explicit and connections are cleaned up.

    Yields (client, repo) so persistence tests can inspect the database.
    """
    db_path = tmp_path / "test_history.db"
    repository = EvaluationRepository(db_path=db_path)
    app.dependency_overrides[get_evaluation_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            yield client, repository
    finally:
        app.dependency_overrides.pop(get_evaluation_repository, None)


# ---------------------------------------------------------------------------
# Shared request payloads
# MockAmazonClient recognizes B000EXAMPLE and B000TOASTER.
# ---------------------------------------------------------------------------

VALID_NIKE_REQUEST = {
    "product": {
        "name": "Nike Air Max 90",
        "asin": "B000EXAMPLE",
        "retailer_name": "Kohl's",
        "retailer_price": 45.00,
    },
    "assumptions": {
        "fba_fee": 7.50,
        "shipping_to_amazon": 2.00,
        "prep_cost": 0.75,
        "cashback_percent": 6.0,
    },
}

VALID_TOASTER_REQUEST = {
    "product": {
        "name": "2-Slice Toaster",
        "asin": "B000TOASTER",
        "retailer_name": "Walmart",
        "retailer_price": 18.00,
    },
}


def post_evaluation(client, request=None) -> dict:
    """Post a valid evaluation and return the parsed JSON response."""
    response = client.post("/evaluate", json=request or VALID_NIKE_REQUEST)
    assert response.status_code == 200, (
        f"Expected 200 from POST /evaluate, got {response.status_code}: "
        f"{response.text}"
    )
    return response.json()


# ---------------------------------------------------------------------------
# GET /evaluations
# ---------------------------------------------------------------------------

def test_list_evaluations_empty_database_returns_empty_list(client_and_repo):
    """
    GET /evaluations on an empty database must return an empty list
    with status 200 — not a 404 or error.
    """
    client, _ = client_and_repo
    response = client.get("/evaluations")

    assert response.status_code == 200
    assert response.json() == []


def test_list_evaluations_returns_all_saved_records(client_and_repo):
    """
    GET /evaluations returns one entry per successful POST /evaluate call.
    """
    client, _ = client_and_repo
    post_evaluation(client)
    post_evaluation(client)
    post_evaluation(client)

    response = client.get("/evaluations")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_evaluations_newest_first(client_and_repo):
    """
    GET /evaluations must return evaluations newest first.
    The most recently saved evaluation appears at index 0.
    """
    client, _ = client_and_repo
    first_id = post_evaluation(client)["evaluation_id"]
    second_id = post_evaluation(client)["evaluation_id"]
    third_id = post_evaluation(client)["evaluation_id"]

    data = client.get("/evaluations").json()

    assert data[0]["id"] == third_id
    assert data[1]["id"] == second_id
    assert data[2]["id"] == first_id


def test_list_evaluations_default_limit_is_50(client_and_repo):
    """
    Without an explicit limit parameter, GET /evaluations returns at most
    50 records even when more exist in the database.
    """
    client, _ = client_and_repo
    for _ in range(55):
        post_evaluation(client)

    response = client.get("/evaluations")

    assert response.status_code == 200
    assert len(response.json()) == 50


def test_list_evaluations_explicit_limit_caps_results(client_and_repo):
    """
    An explicit limit query parameter caps the number of returned records.
    """
    client, _ = client_and_repo
    for _ in range(10):
        post_evaluation(client)

    response = client.get("/evaluations?limit=3")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_evaluations_limit_below_minimum_returns_422(client_and_repo):
    """
    limit=0 violates ge=1 on the Query parameter and must return 422.
    Nothing is persisted — this is a request validation failure.
    """
    client, _ = client_and_repo
    response = client.get("/evaluations?limit=0")
    assert response.status_code == 422


def test_list_evaluations_limit_above_maximum_returns_422(client_and_repo):
    """
    limit=201 violates le=200 on the Query parameter and must return 422.
    """
    client, _ = client_and_repo
    response = client.get("/evaluations?limit=201")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /evaluations/{evaluation_id}
# ---------------------------------------------------------------------------

def test_get_evaluation_by_id_returns_matching_record(client_and_repo):
    """
    GET /evaluations/{id} returns the evaluation with the matching ID
    and HTTP 200.
    """
    client, _ = client_and_repo
    evaluation_id = post_evaluation(client)["evaluation_id"]

    response = client.get(f"/evaluations/{evaluation_id}")

    assert response.status_code == 200
    assert response.json()["id"] == evaluation_id


def test_get_evaluation_by_id_unknown_returns_404(client_and_repo):
    """
    GET /evaluations/{id} returns 404 when no record exists with that ID.
    The response detail must include the requested ID so the caller can
    identify which lookup failed.
    """
    client, _ = client_and_repo
    response = client.get("/evaluations/99999")

    assert response.status_code == 404
    assert "99999" in response.json()["detail"]


def test_get_evaluation_complete_field_mapping(client_and_repo):
    """
    The GET /evaluations/{id} response must include every persisted snapshot
    field with values that match what was submitted and what the pipeline
    calculated.
    """
    client, _ = client_and_repo
    post_data = post_evaluation(client, VALID_NIKE_REQUEST)
    evaluation_id = post_data["evaluation_id"]

    response = client.get(f"/evaluations/{evaluation_id}")
    assert response.status_code == 200
    data = response.json()

    # Identity
    assert data["id"] == evaluation_id

    # Product / retailer
    assert data["product_name"] == "Nike Air Max 90"
    assert data["retailer_name"] == "Kohl's"
    assert data["retailer_price"] == 45.00

    # Amazon snapshot
    assert data["asin"] == "B000EXAMPLE"
    assert data["amazon_title"] == "Nike Air Max 90"
    assert data["amazon_price"] == 89.99
    assert data["amazon_bsr"] == 1500
    assert data["amazon_seller_count"] == 8
    assert data["amazon_review_rating"] == 4.5

    # Cost assumptions — spot check requested values and defaults
    assert data["fba_fee"] == 7.50
    assert data["shipping_to_amazon"] == 2.00
    assert data["prep_cost"] == 0.75
    assert data["cashback_percent"] == 6.0
    assert data["amazon_referral_fee_percent"] == 15.0
    assert data["sales_tax_percent"] == 0.0
    assert data["coupon_discount"] == 0.0

    # Profit result — must match what POST /evaluate returned
    assert data["net_profit"] == post_data["profit_result"]["net_profit"]
    assert data["roi_percent"] == post_data["profit_result"]["roi_percent"]
    assert data["margin_percent"] == post_data["profit_result"]["margin_percent"]
    assert data["total_cost"] == post_data["profit_result"]["total_cost"]
    assert data["total_fees"] == post_data["profit_result"]["total_fees"]
    assert data["cashback_amount"] == post_data["profit_result"]["cashback_amount"]

    # Recommendation — must match what POST /evaluate returned
    assert data["recommendation"] == post_data["recommendation"]["recommendation"]
    assert data["recommendation_reasons"] == post_data["recommendation"]["reasons"]


def test_get_evaluation_timestamp_is_timezone_aware(client_and_repo):
    """
    evaluated_at in the GET response must be a timezone-aware ISO 8601 string.
    A naive datetime would lack a UTC offset.
    """
    client, _ = client_and_repo
    evaluation_id = post_evaluation(client)["evaluation_id"]

    response = client.get(f"/evaluations/{evaluation_id}")
    evaluated_at = response.json()["evaluated_at"]

    # FastAPI serializes timezone-aware datetimes with +00:00 or Z suffix
    is_aware = "+" in evaluated_at or evaluated_at.endswith("Z")
    assert is_aware, (
        f"evaluated_at is not timezone-aware: {evaluated_at!r}"
    )

    # Must round-trip back to a timezone-aware datetime object
    parsed = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# GET /evaluations/asin/{asin}
# ---------------------------------------------------------------------------

def test_list_by_asin_returns_only_matching_records(client_and_repo):
    """
    GET /evaluations/asin/{asin} returns only evaluations for that ASIN.
    Records for other ASINs must not appear.
    """
    client, _ = client_and_repo
    post_evaluation(client, VALID_NIKE_REQUEST)
    post_evaluation(client, VALID_NIKE_REQUEST)
    post_evaluation(client, VALID_TOASTER_REQUEST)

    response = client.get("/evaluations/asin/B000EXAMPLE")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(r["asin"] == "B000EXAMPLE" for r in data)


def test_list_by_asin_unknown_asin_returns_empty_list(client_and_repo):
    """
    GET /evaluations/asin/{asin} returns an empty list when no records
    exist for the requested ASIN — not a 404.
    """
    client, _ = client_and_repo
    response = client.get("/evaluations/asin/DOESNOTEXIST")

    assert response.status_code == 200
    assert response.json() == []


def test_list_by_asin_newest_first(client_and_repo):
    """
    GET /evaluations/asin/{asin} returns evaluations newest first.
    """
    client, _ = client_and_repo
    first_id = post_evaluation(client)["evaluation_id"]
    second_id = post_evaluation(client)["evaluation_id"]

    data = client.get("/evaluations/asin/B000EXAMPLE").json()

    assert data[0]["id"] == second_id
    assert data[1]["id"] == first_id


def test_list_by_asin_respects_limit(client_and_repo):
    """
    The limit parameter applies to ASIN-filtered results the same way
    it applies to list_all results.
    """
    client, _ = client_and_repo
    for _ in range(5):
        post_evaluation(client)

    response = client.get("/evaluations/asin/B000EXAMPLE?limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_by_asin_excludes_other_asins(client_and_repo):
    """
    ASIN-filtered results for one ASIN must not contain records from
    another ASIN even when both exist in the database.
    """
    client, _ = client_and_repo
    post_evaluation(client, VALID_NIKE_REQUEST)
    post_evaluation(client, VALID_TOASTER_REQUEST)

    nike_data = client.get("/evaluations/asin/B000EXAMPLE").json()
    toaster_data = client.get("/evaluations/asin/B000TOASTER").json()

    assert len(nike_data) == 1
    assert len(toaster_data) == 1
    assert nike_data[0]["asin"] == "B000EXAMPLE"
    assert toaster_data[0]["asin"] == "B000TOASTER"


def test_asin_route_is_not_shadowed_by_id_route(client_and_repo):
    """
    GET /evaluations/asin/B000EXAMPLE must reach the ASIN endpoint,
    not the /evaluations/{evaluation_id} route.

    If route ordering were wrong, FastAPI would attempt to parse
    "B000EXAMPLE" as an integer evaluation_id and return 422.
    This test confirms the ASIN route is registered first and the
    literal segment "asin" is matched before the dynamic int segment.
    """
    client, _ = client_and_repo
    post_evaluation(client, VALID_NIKE_REQUEST)

    response = client.get("/evaluations/asin/B000EXAMPLE")

    # Must reach the ASIN handler and return a list, not a 422
    assert response.status_code == 200
    assert isinstance(response.json(), list)