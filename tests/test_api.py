from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_evaluate_product_success():
    response = client.post("/evaluate", json={
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
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Nike Air Max 90"
    assert data["error"] is None
    assert data["amazon_product"]["asin"] == "B000EXAMPLE"
    assert data["profit_result"]["net_profit"] > 0
    assert data["recommendation"]["recommendation"] in ["BUY", "WATCH", "PASS"]
    assert len(data["recommendation"]["reasons"]) > 0


def test_evaluate_product_no_asin_returns_error():
    response = client.post("/evaluate", json={
        "product": {
            "name": "Unknown Product",
            "retailer_price": 20.00,
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["error"] is not None
    assert data["profit_result"] is None
    assert data["recommendation"] is None


def test_evaluate_product_unknown_asin_returns_error():
    response = client.post("/evaluate", json={
        "product": {
            "name": "Ghost Product",
            "asin": "DOESNOTEXIST",
            "retailer_price": 20.00,
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["error"] is not None


def test_evaluate_product_default_assumptions():
    response = client.post("/evaluate", json={
        "product": {
            "name": "Nike Air Max 90",
            "asin": "B000EXAMPLE",
            "retailer_price": 45.00,
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert data["profit_result"] is not None