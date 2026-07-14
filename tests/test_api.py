from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# --- Success cases ---

def test_evaluate_product_success():
    response = client.post(
        "/evaluate",
        json={
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
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Confirm the old error field is gone entirely.
    assert "error" not in data

    assert data["product_name"] == "Nike Air Max 90"
    assert data["amazon_product"]["asin"] == "B000EXAMPLE"
    assert data["profit_result"]["net_profit"] > 0
    assert data["recommendation"]["recommendation"] in [
        "BUY",
        "WATCH",
        "PASS",
    ]
    assert len(data["recommendation"]["reasons"]) > 0


def test_evaluate_product_default_assumptions():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Nike Air Max 90",
                "asin": "B000EXAMPLE",
                "retailer_price": 45.00,
            }
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "error" not in data
    assert data["profit_result"] is not None


# --- Failure cases: HTTP translation ---

def test_evaluate_product_no_asin_returns_422():
    """
    MissingAsinError raised by SourcingService should translate
    to HTTP 422 Unprocessable Entity at the API layer.
    The detail field should be informative enough for a client to act on.
    """
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Unknown Product",
                "retailer_price": 20.00,
            }
        },
    )

    assert response.status_code == 422
    data = response.json()

    assert "detail" in data
    assert "Unknown Product" in data["detail"]


def test_evaluate_product_unknown_asin_returns_404():
    """
    AmazonProductNotFoundError raised by SourcingService should translate
    to HTTP 404 Not Found at the API layer.
    The detail field should include the ASIN that was not found.
    """
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Ghost Product",
                "asin": "DOESNOTEXIST",
                "retailer_price": 20.00,
            }
        },
    )

    assert response.status_code == 404
    data = response.json()

    assert "detail" in data
    assert "DOESNOTEXIST" in data["detail"]


def test_evaluate_product_no_retailer_price_returns_422():
    """
    MissingRetailerPriceError raised by SourcingService should translate
    to HTTP 422 Unprocessable Entity at the API layer.

    Tested separately from missing ASIN because both map to 422 but
    are distinct domain failures with distinct messages.
    """
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Nike Air Max 90",
                "asin": "B000EXAMPLE",
            }
        },
    )

    assert response.status_code == 422
    data = response.json()

    assert "detail" in data
    assert "Nike Air Max 90" in data["detail"]


# --- Failure cases: request validation ---

def test_evaluate_rejects_negative_retailer_price():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Test Product",
                "asin": "B000TEST01",
                "retailer_price": -10.00,
            }
        },
    )

    assert response.status_code == 422


def test_evaluate_rejects_negative_cost_assumption():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Test Product",
                "asin": "B000TEST01",
                "retailer_price": 20.00,
            },
            "assumptions": {
                "shipping_to_amazon": -5.00,
            },
        },
    )

    assert response.status_code == 422

def test_evaluate_rejects_zero_amazon_bsr():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Test Product",
                "asin": "B000TEST01",
                "retailer_price": 20.00,
                "amazon_bsr": 0,
            }
        },
    )

    assert response.status_code == 422


def test_evaluate_rejects_cashback_above_100_percent():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Test Product",
                "asin": "B000TEST01",
                "retailer_price": 20.00,
            },
            "assumptions": {
                "cashback_percent": 101,
            },
        },
    )

    assert response.status_code == 422


def test_evaluate_rejects_sales_tax_above_30_percent():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Test Product",
                "asin": "B000TEST01",
                "retailer_price": 20.00,
            },
            "assumptions": {
                "sales_tax_percent": 31,
            },
        },
    )

    assert response.status_code == 422


def test_evaluate_rejects_return_risk_above_100_percent():
    response = client.post(
        "/evaluate",
        json={
            "product": {
                "name": "Test Product",
                "asin": "B000TEST01",
                "retailer_price": 20.00,
            },
            "assumptions": {
                "return_risk_percent": 101,
            },
        },
    )

    assert response.status_code == 422