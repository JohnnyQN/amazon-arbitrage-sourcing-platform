from datetime import date

from app.amazon.amazon_client import MockAmazonClient
from app.models.product import Product
from app.services.recommendation_engine import Recommendation, RecommendationConfig
from app.services.sourcing_service import CostAssumptions, SourcingService


def make_nike_product():
    return Product(
        name="Nike Air Max 90",
        brand="Nike",
        asin="B000EXAMPLE",
        retailer_name="Kohl's",
        retailer_price=45.00,
        date_found=date(2026, 6, 30),
    )


def make_service(config=None):
    return SourcingService(
        amazon_client=MockAmazonClient(),
        recommendation_config=config,
    )


def test_evaluate_product_success():
    service = make_service()
    product = make_nike_product()
    assumptions = CostAssumptions(
        fba_fee=7.50,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
    )

    result = service.evaluate_product(product, assumptions)

    assert result.error is None
    assert result.amazon_product is not None
    assert result.amazon_product.asin == "B000EXAMPLE"
    assert result.profit_input is not None
    assert result.profit_input.buy_cost == 45.00
    assert result.profit_input.amazon_sell_price == 89.99
    assert result.profit_result is not None
    assert result.profit_result.net_profit > 0
    assert result.recommendation is not None


def test_evaluate_product_returns_recommendation():
    service = make_service()
    product = make_nike_product()
    assumptions = CostAssumptions(
        fba_fee=7.50,
        shipping_to_amazon=2.00,
        prep_cost=0.75,
        cashback_percent=6.0,
    )

    result = service.evaluate_product(product, assumptions)

    assert result.recommendation.recommendation in [
        Recommendation.BUY,
        Recommendation.WATCH,
        Recommendation.PASS,
    ]
    assert len(result.recommendation.reasons) > 0


def test_evaluate_product_custom_config_affects_recommendation():
    # Strict config — very high ROI bar
    strict_config = RecommendationConfig(
        min_roi_for_buy=80.0,
        min_roi_for_watch=50.0,
    )
    service = make_service(config=strict_config)
    product = make_nike_product()
    assumptions = CostAssumptions(fba_fee=7.50, cashback_percent=6.0)

    result = service.evaluate_product(product, assumptions)

    # Nike shoe bought at $45, sold at $89.99 won't hit 80% ROI,
    # but it does exceed the 50% WATCH threshold.
    assert result.recommendation.recommendation == Recommendation.WATCH


def test_evaluate_product_no_asin():
    service = make_service()
    product = Product(name="Mystery Item", retailer_price=20.00)

    result = service.evaluate_product(product, CostAssumptions())

    assert result.error == "No matching Amazon product found for ASIN."
    assert result.profit_result is None
    assert result.recommendation is None


def test_evaluate_product_asin_not_found():
    service = make_service()
    product = Product(
        name="Ghost Product",
        asin="DOESNOTEXIST",
        retailer_price=20.00,
    )

    result = service.evaluate_product(product, CostAssumptions())

    assert result.error == "No matching Amazon product found for ASIN."
    assert result.recommendation is None


def test_evaluate_product_no_retailer_price():
    service = make_service()
    product = Product(name="Nike Air Max 90", asin="B000EXAMPLE")

    result = service.evaluate_product(product, CostAssumptions())

    assert result.error == "Product has no retailer price."
    assert result.recommendation is None