import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.api.dependencies import get_evaluation_repository
from app.main import app
from app.repositories.evaluation_repository import EvaluationRepository


# --- Fixtures ---

@pytest.fixture
def client_and_repo(tmp_path: Path):
    """
    Provides a TestClient with the EvaluationRepository dependency
    overridden to use a temporary database.

    Uses try/finally to remove only the get_evaluation_repository override,
    leaving any other overrides untouched. TestClient is used as a context
    manager so its lifespan is explicit and connections are cleaned up.

    Yields (client, repo) so persistence tests can inspect the database.
    """
    db_path = tmp_path / "test_api.db"
    repository = EvaluationRepository(db_path=db_path)
    app.dependency_overrides[get_evaluation_repository] = lambda: repository
    try:
        with TestClient(app) as client:
            yield client, repository
    finally:
        app.dependency_overrides.pop(get_evaluation_repository, None)


# --- Shared request payloads ---

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


# --- Success: response shape ---

def test_evaluate_product_success(client_and_repo):
    client, _ = client_and_repo
    response = client.post("/evaluate", json=VALID_NIKE_REQUEST)

    assert response.status_code == 200
    data = response.json()

    assert "error" not in data
    assert "evaluation_id" in data
    assert isinstance(data["evaluation_id"], int)
    assert data["product_name"] == "Nike Air Max 90"
    assert data["amazon_product"]["asin"] == "B000EXAMPLE"
    assert data["profit_result"]["net_profit"] > 0
    assert data["recommendation"]["recommendation"] in ["BUY", "WATCH", "PASS"]
    assert len(data["recommendation"]["reasons"]) > 0


def test_evaluate_product_default_assumptions(client_and_repo):
    client, _ = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Nike Air Max 90",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert "error" not in data
    assert data["profit_result"] is not None


# --- Success: persistence ---

def test_successful_evaluation_persists_one_row(client_and_repo):
    """
    A successful /evaluate request must save exactly one row.
    """
    client, repo = client_and_repo
    assert len(repo.list_all()) == 0

    client.post("/evaluate", json=VALID_NIKE_REQUEST)

    assert len(repo.list_all()) == 1


def test_response_evaluation_id_matches_saved_row(client_and_repo):
    """
    The evaluation_id in the response must match the ID of the row
    actually written to the database.
    """
    client, repo = client_and_repo
    response = client.post("/evaluate", json=VALID_NIKE_REQUEST)

    evaluation_id = response.json()["evaluation_id"]
    saved = repo.get_by_id(evaluation_id)

    assert saved is not None
    assert saved.id == evaluation_id


def test_persisted_values_are_correct(client_and_repo):
    """
    Values written to the database must match what was sent in the request
    and what the pipeline calculated.
    """
    client, repo = client_and_repo
    response = client.post("/evaluate", json=VALID_NIKE_REQUEST)
    data = response.json()

    saved = repo.get_by_id(data["evaluation_id"])

    assert saved is not None
    assert saved.product_name == "Nike Air Max 90"
    assert saved.asin == "B000EXAMPLE"
    assert saved.retailer_price == 45.00
    assert saved.fba_fee == 7.50
    assert saved.cashback_percent == 6.0
    assert saved.net_profit == data["profit_result"]["net_profit"]
    assert saved.recommendation == data["recommendation"]["recommendation"]
  


def test_multiple_successful_requests_create_multiple_records(client_and_repo):
    """
    Each successful /evaluate call must persist exactly one row.
    Three calls must produce three rows with distinct IDs.
    """
    client, repo = client_and_repo

    ids = []
    for _ in range(3):
        response = client.post("/evaluate", json=VALID_NIKE_REQUEST)
        assert response.status_code == 200
        ids.append(response.json()["evaluation_id"])

    assert len(set(ids)) == 3
    assert len(repo.list_all()) == 3


# --- Domain failure cases: correct status codes and nothing persisted ---

def test_missing_asin_returns_422_with_detail(client_and_repo):
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {"name": "Unknown Product", "retailer_price": 20.00}
    })

    assert response.status_code == 422
    assert "Unknown Product" in response.json()["detail"]
    assert repo.list_all() == []


def test_unknown_asin_returns_404_with_detail(client_and_repo):
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Ghost Product",
            "asin": "DOESNOTEXIST",
            "retailer_price": 20.00,
        }
    })

    assert response.status_code == 404
    assert "DOESNOTEXIST" in response.json()["detail"]
    assert repo.list_all() == []


def test_missing_retailer_price_returns_422_with_detail(client_and_repo):
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {"name": "Nike Air Max 90", "asin": "B000EXAMPLE"}
    })

    assert response.status_code == 422
    assert "Nike Air Max 90" in response.json()["detail"]
    assert repo.list_all() == []


# --- Pydantic validation: invalid inputs are rejected before the pipeline runs ---

def test_negative_retailer_price_returns_422(client_and_repo):
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Test Product",
            "asin": "B000EXAMPLE",
            "retailer_price": -10.00,
        }
    })

    assert response.status_code == 422
    assert repo.list_all() == []


def test_negative_cost_assumption_returns_422(client_and_repo):
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Test Product",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
        },
        "assumptions": {"fba_fee": -1.00}
    })

    assert response.status_code == 422
    assert repo.list_all() == []


def test_zero_amazon_bsr_returns_422(client_and_repo):
    """
    BSR of 0 is not a valid Amazon value. gt=0 on amazon_bsr must reject it.
    """
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Test Product",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
            "amazon_bsr": 0,
        }
    })

    assert response.status_code == 422
    assert repo.list_all() == []


def test_cashback_above_100_returns_422(client_and_repo):
    """
    Cashback percent above 100 is nonsensical. le=100 must reject it.
    """
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Test Product",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
        },
        "assumptions": {"cashback_percent": 101.0}
    })

    assert response.status_code == 422
    assert repo.list_all() == []


def test_sales_tax_above_30_returns_422(client_and_repo):
    """
    Sales tax above 30% is outside any real-world jurisdiction.
    le=30 must reject it to catch typos like 80 instead of 8.0.
    """
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Test Product",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
        },
        "assumptions": {"sales_tax_percent": 31.0}
    })

    assert response.status_code == 422
    assert repo.list_all() == []


def test_return_risk_above_100_returns_422(client_and_repo):
    """
    Return risk above 100% is mathematically impossible.
    le=100 must reject it.
    """
    client, repo = client_and_repo
    response = client.post("/evaluate", json={
        "product": {
            "name": "Test Product",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
        },
        "assumptions": {"return_risk_percent": 101.0}
    })

    assert response.status_code == 422
    assert repo.list_all() == []